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
        PROJECT_ID = "niyamaddin"
        REGION = "us-central1"
        CLUSTER_NAME = "automation-cluster"
        STAGING_BUCKET = "niyamaddin-dataproc-staging"
        SONAR_SERVER_NAME = "SonarQube"

        PYTHONBUFFERED = '1'
        ETS_TOOLKIT = 'null'
        VTK_PARSER_VERBOSE = 'true'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup & Install') {
            steps {
                container('gcloud') {
                    sh '''
                    set -euxo pipefail
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip setuptools wheel
                    python -m pip install numpy "vtk<9.3" pillow pytest pytest-timeout traitsui
                    python -m pip install --no-build-isolation -v .
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                container('gcloud') {
                sh '''
                set -euxo pipefail
                . .venv/bin/activate
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
                echo "Deploying to Dataproc Cluster: ${CLUSTER_NAME}"
            }
        }
    
    }
    post {
        always {
            echo 'Pipeline execution finished'
        }
        success {
            echo 'CI/CD completed successfully'
        }
        failure {
            echo 'Pipeline failed'
        }
    }
}