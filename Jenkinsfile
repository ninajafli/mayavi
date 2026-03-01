pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: python
    image: python:3.11
    command: ["sleep"]
    args: ["99d"]
  - name: gcloud
    image: google/cloud-sdk:slim
    command: ["sleep"]
    args: ["99d"]
'''
        }
    }

    environment {
        PROJECT_ID = "niyamaddin"
        REGION     = "us-central1"
        CLUSTER    = "automation-cluster"
        STAGING_BUCKET = "gs://niyamaddin-dataproc-staging"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                container('python') {
                    script {
                        sh '''
                            python -m pip install --upgrade pip setuptools wheel
                            python -m pip install numpy "vtk<9.3" pillow pytest pytest-timeout traitsui
                            python -m pip install --no-build-isolation -v .
                            pytest -v --timeout=10 --pyargs mayavi
                        '''
                    }
            }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner -Dsonar.projectKey=mayavi-repo -Dsonar.sources=.'
                }
            }
        }

        stage("Quality Gate") {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Deploy to Hadoop (Dataproc)') {
            steps {
                container('gcloud') {
                    script {
                        echo "SonarQube passed! Deploying to Dataproc..."
                        sh "gsutil -m cp -r . ${STAGING_BUCKET}/deploy/"
                        sh """
                            gcloud dataproc jobs submit pyspark ${STAGING_BUCKET}/deploy/examples/mayavi/standalone/dots.py \
                                --cluster=${CLUSTER} \
                                --region=${REGION}
                        """
                    }
                }
            }
        }
    }
}