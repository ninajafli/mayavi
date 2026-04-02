pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: ci-cd-admin
  containers:
  - name: gcloud
    image: google/cloud-sdk:slim
    command: ["cat"]
    tty: true
'''
        }
    }

    environment {
        PROJECT_ID         = "niyamaddin"
        REGION             = "us-east4"
        CLUSTER_NAME       = "automation-cluster"
        STAGING_BUCKET     = "niyamaddin-dataproc-staging"
        SONAR_SERVER_NAME  = "SonarQube"
    }

    stages {
        stage('Setup') {
            steps {
                container('gcloud') {
                    sh '''
                    set -eux
                    apt-get update && apt-get install -y default-jre
                    gcloud config set project ${PROJECT_ID}
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('gcloud') {
                    script {
                        def scannerHome = tool 'SonarScanner'
                        withSonarQubeEnv("${SONAR_SERVER_NAME}") {
                            sh """
                            ${scannerHome}/bin/sonar-scanner \
                            -Dsonar.projectKey=mayavi-python-project \
                            -Dsonar.sources=. \
                            -Dsonar.python.version=3
                            """
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Run Hadoop Job') {
            steps {
                container('gcloud') {
                    sh '''
                    set -eux

                    gsutil -m rm -r "gs://${STAGING_BUCKET}/deploy/" 2>/dev/null || true
                    gsutil -m rm -r "gs://${STAGING_BUCKET}/results/" 2>/dev/null || true

                    gsutil cp mapper.py reducer.py "gs://${STAGING_BUCKET}/deploy/"
                    find . -name '*.py' -not -name 'mapper.py' -not -name 'reducer.py' \
                        | gsutil -m cp -I "gs://${STAGING_BUCKET}/deploy/input/"

                    # Copy input files from GCS into HDFS for data-local reads
                    gcloud dataproc jobs submit hadoop \
                        --cluster="${CLUSTER_NAME}" \
                        --region="${REGION}" \
                        --project="${PROJECT_ID}" \
                        --class=org.apache.hadoop.tools.DistCp \
                        -- \
                        -overwrite \
                        "gs://${STAGING_BUCKET}/deploy/input/" \
                        "hdfs:///tmp/mr-input/"

                    # Streaming job reads/writes HDFS (local I/O, no GCS overhead)
                    gcloud dataproc jobs submit hadoop \
                        --cluster="${CLUSTER_NAME}" \
                        --region="${REGION}" \
                        --project="${PROJECT_ID}" \
                        --jar=file:///usr/lib/hadoop/hadoop-streaming.jar \
                        -- \
                        -D mapreduce.input.fileinputformat.input.dir.recursive=true \
                        -files "gs://${STAGING_BUCKET}/deploy/mapper.py,gs://${STAGING_BUCKET}/deploy/reducer.py" \
                        -mapper "python3 mapper.py" \
                        -reducer "python3 reducer.py" \
                        -input "hdfs:///tmp/mr-input/" \
                        -output "hdfs:///tmp/mr-output/line-counts"

                    # Copy results from HDFS back to GCS for persistent storage
                    gcloud dataproc jobs submit hadoop \
                        --cluster="${CLUSTER_NAME}" \
                        --region="${REGION}" \
                        --project="${PROJECT_ID}" \
                        --class=org.apache.hadoop.tools.DistCp \
                        -- \
                        "hdfs:///tmp/mr-output/line-counts/" \
                        "gs://${STAGING_BUCKET}/results/line-counts/"

                    echo "==========================================="
                    echo "  Hadoop MapReduce Job Results"
                    echo "==========================================="
                    gsutil cat "gs://${STAGING_BUCKET}/results/line-counts/part-*"
                    echo "==========================================="
                    echo "Results saved to: gs://${STAGING_BUCKET}/results/line-counts/"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution finished.'
        }
        success {
            echo 'CI/CD Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
    }
}
