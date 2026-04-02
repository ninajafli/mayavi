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

                    rm -rf .git .venv __pycache__ .scannerwork 2>/dev/null || true
                    find . -name '*.pyc' -delete 2>/dev/null || true

                    gsutil -m rm -r "gs://${STAGING_BUCKET}/deploy/" 2>/dev/null || true
                    gsutil -m rm -r "gs://${STAGING_BUCKET}/results/" 2>/dev/null || true
                    gsutil -m cp -r . "gs://${STAGING_BUCKET}/deploy/"

                    gcloud dataproc jobs submit pyspark \
                        "gs://${STAGING_BUCKET}/deploy/line_counter.py" \
                        --cluster="${CLUSTER_NAME}" \
                        --region="${REGION}" \
                        --project="${PROJECT_ID}" \
                        -- "gs://${STAGING_BUCKET}/deploy/" "gs://${STAGING_BUCKET}/results/line-counts"

                    echo "==========================================="
                    echo "  Hadoop MapReduce Job Results"
                    echo "==========================================="
                    gsutil cat "gs://${STAGING_BUCKET}/results/line-counts/part-00000"
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
