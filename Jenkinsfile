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
        stage('Install & Test') {
            steps {
                container('gcloud') {
                    sh '''
                    set -eux
                    # Install build dependencies
                    apt-get update
                    apt-get install -y \
                        python3-venv \
                        zip \
                        libgl1 \
                        libglu1-mesa \
                        libxt6 \
                        libxrender1 \
                        libxext6 \
                        libfontconfig1 \
                        libglib2.0-0 \
                        default-jre
                    
                    # Setup Environment
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip setuptools wheel
                    python -m pip install --upgrade --force-reinstall "numpy<2"
                    python -m pip install "vtk<9.3" pillow pytest pytest-timeout traitsui
                    
                    # Install Mayavi
                    python -m pip install --no-build-isolation -v .
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

        stage('Deploy to Hadoop') {
            steps {
                container('gcloud') {
                    script {
                        sh "gsutil -m cp -r . ${STAGING_BUCKET}/deploy/"
                        sh """
                            gcloud dataproc jobs submit pyspark gs://${STAGING_BUCKET}/deploy/examples/mayavi/standalone.py \
                                --cluster=${CLUSTER_NAME} \
                                --region=${REGION}
                        """
                    }
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