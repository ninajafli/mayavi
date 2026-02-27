pipeline {
    agent {
        label 'jenkins-jenkins-agent'
    }

    stages {
        stage('Build') {
            steps {
                echo 'Building on a dedicated GKE worker pod...'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
            }
        }
    }
}