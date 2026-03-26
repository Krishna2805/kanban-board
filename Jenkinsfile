// ─────────────────────────────────────────────────────────────────────────────
// Jenkinsfile — Mini Kanban Board CI/CD Pipeline (WINDOWS VERSION)
// Uses `bat` instead of `sh` throughout — required for Windows Jenkins agents.
// ─────────────────────────────────────────────────────────────────────────────

pipeline {

    agent any

    environment {
        IMAGE_NAME = 'kanban-board'
    }

    stages {

        // ── Stage 1: Checkout ─────────────────────────────────────────────────
        stage('Stage 1 \u2014 Checkout') {
            steps {
                echo "===================================================="
                echo " STAGE 1: Checkout"
                echo " Branch : ${env.BRANCH_NAME}"
                echo " Build  : #${env.BUILD_NUMBER}"
                echo "===================================================="
                checkout scm
            }
        }

        // ── Stage 2: Install Dependencies ────────────────────────────────────
        stage('Stage 2 \u2014 Install Dependencies') {
            steps {
                echo "===================================================="
                echo " STAGE 2: Installing Python dependencies"
                echo "===================================================="
                bat '''
                    python -m venv venv
                    call venv\\Scripts\\activate.bat
                    python -m pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    pip list --format=columns
                '''
            }
        }

        // ── Stage 3: Quality Gate ─────────────────────────────────────────────
        stage('Stage 3 \u2014 Quality Gate') {
            steps {
                echo "===================================================="
                echo " STAGE 3: Running automated tests (Pytest)"
                echo "===================================================="
                bat '''
                    call venv\\Scripts\\activate.bat
                    python -m pytest test_app.py -v --tb=short
                '''
            }
            post {
                success {
                    echo "\u2705 All tests passed — proceeding to build."
                }
                failure {
                    echo "\u26A8 Tests FAILED — pipeline aborted. No build. No deployment."
                }
            }
        }

        // ── Stage 4: Build Docker Image ───────────────────────────────────────
        stage('Stage 4 \u2014 Build Docker Image') {
            steps {
                script {
                    def envName    = (env.BRANCH_NAME == 'main') ? 'production' : 'development'
                    def appVersion = "v1.${env.BUILD_NUMBER}"

                    echo "===================================================="
                    echo " STAGE 4: Building Docker image"
                    echo " Image   : ${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    echo " Env     : ${envName}"
                    echo " Version : ${appVersion}"
                    echo "===================================================="

                    bat """
                        docker build ^
                            --build-arg APP_VERSION=${appVersion} ^
                            --build-arg ENV_NAME=${envName} ^
                            -t ${IMAGE_NAME}:${env.BUILD_NUMBER} ^
                            -t ${IMAGE_NAME}:latest-${envName} ^
                            .
                    """
                }
            }
        }

        // ── Stage 5: Deploy ───────────────────────────────────────────────────
        stage('Stage 5 \u2014 Deploy') {
            steps {
                script {
                    def appVersion = "v1.${env.BUILD_NUMBER}"

                    if (env.BRANCH_NAME == 'main') {

                        echo "===================================================="
                        echo " STAGE 5: Deploying to PRODUCTION (port 5000)"
                        echo "===================================================="

                        bat """
                            docker stop kanban-prod 2>nul & exit /b 0
                            docker rm   kanban-prod 2>nul & exit /b 0
                            docker run -d ^
                                --name kanban-prod ^
                                --restart unless-stopped ^
                                -p 5000:5000 ^
                                -e APP_VERSION=${appVersion} ^
                                -e ENV_NAME=production ^
                                ${IMAGE_NAME}:${env.BUILD_NUMBER}
                        """
                        echo "\u2705 Production app live at http://localhost:5000"

                    } else if (env.BRANCH_NAME == 'dev') {

                        echo "===================================================="
                        echo " STAGE 5: Deploying to DEVELOPMENT (port 5001)"
                        echo "===================================================="

                        bat """
                            docker stop kanban-dev 2>nul & exit /b 0
                            docker rm   kanban-dev 2>nul & exit /b 0
                            docker run -d ^
                                --name kanban-dev ^
                                --restart unless-stopped ^
                                -p 5001:5000 ^
                                -e APP_VERSION=${appVersion} ^
                                -e ENV_NAME=development ^
                                ${IMAGE_NAME}:${env.BUILD_NUMBER}
                        """
                        echo "\u2705 Development app live at http://localhost:5001"

                    } else {
                        echo "Branch '${env.BRANCH_NAME}' is not a deploy target. Skipping."
                    }
                }
            }
        }

    } // end stages

    post {
        success {
            echo "PIPELINE SUCCEEDED - Build #${env.BUILD_NUMBER} on branch ${env.BRANCH_NAME}"
        }
        failure {
            echo "PIPELINE FAILED - Build #${env.BUILD_NUMBER}. Check Stage 3 output."
        }
        always {
            bat 'if exist venv rmdir /s /q venv'
        }
    }

}