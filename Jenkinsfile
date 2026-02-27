pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: gcloud
    image: google/cloud-sdk:slim
    command: ["cat"]
    tty: true
'''
        }
    }

    environment {
        // Project Specifics
        PROJECT_ID         = "niyamaddin"
        REGION             = "us-central1"
        CLUSTER_NAME       = "automation-cluster"
        STAGING_BUCKET     = "niyamaddin-dataproc-staging"
        
        // SonarQube Config
        SONAR_SERVER_NAME  = "SonarQube" 
        
        // Python/Mayavi Config
        PYTHONUNBUFFERED   = '1'
        ETS_TOOLKIT        = 'null'
        VTK_PARSER_VERBOSE = 'true'
    }

    stages {
        stage('Checkout') {
            steps {
                container('gcloud') {
                    checkout scm
                }
            }
        }

        stage('Install & Test') {
            steps {
                container('gcloud') {
                    sh '''
                    set -euxo pipefail
                    # Install build dependencies
                    apt-get update && apt-get install -y python3-venv zip
                    
                    # Setup Environment
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip setuptools wheel
                    python -m pip install numpy "vtk<9.3" pillow pytest pytest-timeout traitsui
                    
                    # Install Mayavi
                    python -m pip install --no-build-isolation -v .
                    
                    # Run Headless Tests
                    pytest -v --timeout=10 --pyargs mayavi
                    pytest -v --timeout=60 --pyargs tvtk
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
                            -Dsonar.language=py \
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

        stage('Deploy to Hadoop') {
            steps {
                container('gcloud') {
                    echo "Deploying to Dataproc Cluster: ${CLUSTER_NAME}"
                    sh """
                    gcloud storage cp examples/mayavi/mlab/contour.py gs://${STAGING_BUCKET}/scripts/main.py

                    gcloud dataproc jobs submit pyspark gs://${STAGING_BUCKET}/scripts/main.py \
                        --cluster=${CLUSTER_NAME} \
                        --region=${REGION} \
                        --properties="spark.pyspark.python=python3"
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution finished'
        }
        success {
            echo 'Mayavi CI/CD completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for YAML errors or test failures.'
        }
    }
}