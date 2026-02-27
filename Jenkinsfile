pipeline {
    agent {
        label 'jenkins-jenkins-agent'
    }

    environment {
        PROJECT_ID = "niyamaddin"
        REGION = "us-central1"
        CLUSTER_NAME = "automation-cluster"
        STAGING_BUCKET = "niyamaddin-dataproc-staging"
        SONAR_SERVER_NAME = "SonarQube"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Build & Package') {
            echo 'Compiling project and building JAR...'
            sh 'mvn clean package -DskipTests'
        }
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv("${SONAR_SERVER_NAME}") {
                        sh """
                        ${scannerHome}/bin/sonar-scanner \
                        -Dsonar.projectKey=mayavi-project \
                        -Dsonar.sources=src/main/java \
                        -Dsonar.java.binaries=target/classes
                        """
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
        stage('Upload Artifact') {
            steps {
                echo 'Uploading JAR to GCS Staging Bucket...'
                sh "gcloud storage cp target/*.jar gs://${STAGING_BUCKET}/artifacts/mayavi.jar"
            }
        }

        stage('Deploy to Hadoop') {
            steps {
                echo "Submitting Spark job to cluster: ${CLUSTER_NAME}"
                sh """
                gcloud dataproc jobs submit spark \
                    --cluster=${CLUSTER_NAME} \
                    --region=${REGION} \
                    --jars=gs://${STAGING_BUCKET}/artifacts/mayavi.jar \
                    --class=com.example.MainClass \
                    -- 1000
                """
            }
        }
    }
    post {
        always {
            echo 'Pipeline execution finished'
        }
        success {
            echo 'Project successfully analyzed and deployed to Hadoop'
        }
        failure {
            echo 'Pipeline failed'
        }
    }
}