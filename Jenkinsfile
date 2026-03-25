// ─────────────────────────────────────────────────────────────────────────────
// Jenkinsfile — Mini Kanban Board CI/CD Pipeline
// DevOps University Project
//
// Pipeline Stages:
//   1 — Checkout          Pull latest code from GitHub
//   2 — Install           Install Python dependencies into a virtualenv
//   3 — Quality Gate      Run Pytest; ABORT pipeline on any test failure
//   4 — Build             Build and tag a versioned Docker image
//   5 — Deploy            Route to dev (port 5001) or prod (port 5000)
//
// Branch → Environment mapping:
//   main  →  production  (port 5000, container: kanban-prod)
//   dev   →  development (port 5001, container: kanban-dev)
//   other →  build + test only, no deployment
// ─────────────────────────────────────────────────────────────────────────────

pipeline {

    agent any

    // ── Global pipeline variables ─────────────────────────────────────────────
    environment {
        IMAGE_NAME = 'kanban-board'
        // APP_VERSION and ENV_NAME are computed per-stage in the script blocks below
    }

    stages {

        // ─────────────────────────────────────────────────────────────────────
        // STAGE 1 — Checkout
        // Pull the latest commit from GitHub via the configured SCM.
        // Jenkins Multibranch Pipeline automatically sets env.BRANCH_NAME.
        // ─────────────────────────────────────────────────────────────────────
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

        // ─────────────────────────────────────────────────────────────────────
        // STAGE 2 — Install Dependencies
        // Create an isolated Python virtual environment and install packages.
        // Using a venv avoids permission issues on shared Jenkins agents.
        // ─────────────────────────────────────────────────────────────────────
        stage('Stage 2 \u2014 Install Dependencies') {
            steps {
                echo "===================================================="
                echo " STAGE 2: Installing Python dependencies"
                echo "===================================================="
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    echo "Installed packages:"
                    pip list --format=columns
                '''
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // STAGE 3 — Quality Gate (Automated Tests)
        //
        // THIS IS THE PIPELINE'S SAFETY NET.
        // If any test fails, Pytest exits with a non-zero code, Jenkins marks
        // this stage as FAILED, and Stages 4 and 5 are NEVER executed.
        // The running container is left completely untouched.
        //
        // To demo a failure: change 'todo' → 'done' in test_app.py and push.
        // ─────────────────────────────────────────────────────────────────────
        stage('Stage 3 \u2014 Quality Gate') {
            steps {
                echo "===================================================="
                echo " STAGE 3: Running automated tests (Pytest)"
                echo "===================================================="
                sh '''
                    . venv/bin/activate
                    python3 -m pytest test_app.py -v --tb=short
                '''
            }
            post {
                success {
                    echo "\u2705 All tests passed — proceeding to build."
                }
                failure {
                    echo "\u26A8\uFE0F  Tests FAILED — pipeline aborted. No build. No deployment."
                    echo "    Fix the failing test and re-push to re-trigger the pipeline."
                }
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // STAGE 4 — Build Docker Image
        //
        // Tags the image with TWO tags:
        //   kanban-board:<BUILD_NUMBER>  — immutable, unique per build
        //   kanban-board:latest-<env>    — floating "latest" for each environment
        //
        // --build-arg injects APP_VERSION and ENV_NAME into the image so
        // the running container always knows where it came from.
        // ─────────────────────────────────────────────────────────────────────
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

                    sh """
                        docker build \\
                            --build-arg APP_VERSION=${appVersion} \\
                            --build-arg ENV_NAME=${envName} \\
                            -t ${IMAGE_NAME}:${env.BUILD_NUMBER} \\
                            -t ${IMAGE_NAME}:latest-${envName} \\
                            .
                    """
                }
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // STAGE 5 — Deploy
        //
        // Branch-based routing:
        //   main  →  stop kanban-prod, start new container on port 5000
        //   dev   →  stop kanban-dev,  start new container on port 5001
        //   other →  skip deployment (feature branches build but don't deploy)
        //
        // "|| true" on stop/rm prevents failure if no container is running yet.
        // --restart unless-stopped ensures the container survives a reboot.
        // ─────────────────────────────────────────────────────────────────────
        stage('Stage 5 \u2014 Deploy') {
            steps {
                script {
                    def appVersion = "v1.${env.BUILD_NUMBER}"

                    if (env.BRANCH_NAME == 'main') {

                        echo "===================================================="
                        echo " STAGE 5: Deploying to PRODUCTION (port 5000)"
                        echo "===================================================="

                        sh """
                            echo "Stopping existing production container (if any)..."
                            docker stop kanban-prod 2>/dev/null || true
                            docker rm   kanban-prod 2>/dev/null || true

                            echo "Starting new production container..."
                            docker run -d \\
                                --name kanban-prod \\
                                --restart unless-stopped \\
                                -p 5000:5000 \\
                                -e APP_VERSION=${appVersion} \\
                                -e ENV_NAME=production \\
                                ${IMAGE_NAME}:${env.BUILD_NUMBER}

                            echo "Production container status:"
                            docker ps --filter name=kanban-prod --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
                        """

                        echo "\u2705 Production app live at http://localhost:5000"

                    } else if (env.BRANCH_NAME == 'dev') {

                        echo "===================================================="
                        echo " STAGE 5: Deploying to DEVELOPMENT (port 5001)"
                        echo "===================================================="

                        sh """
                            echo "Stopping existing development container (if any)..."
                            docker stop kanban-dev 2>/dev/null || true
                            docker rm   kanban-dev 2>/dev/null || true

                            echo "Starting new development container..."
                            docker run -d \\
                                --name kanban-dev \\
                                --restart unless-stopped \\
                                -p 5001:5000 \\
                                -e APP_VERSION=${appVersion} \\
                                -e ENV_NAME=development \\
                                ${IMAGE_NAME}:${env.BUILD_NUMBER}

                            echo "Development container status:"
                            docker ps --filter name=kanban-dev --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
                        """

                        echo "\u2705 Development app live at http://localhost:5001"

                    } else {

                        echo "===================================================="
                        echo " STAGE 5: Branch '${env.BRANCH_NAME}' is not a deploy target."
                        echo " Skipping deployment. Build artifact is available."
                        echo "===================================================="

                    }
                }
            }
        }

    } // end stages

    // ── Post-pipeline actions ─────────────────────────────────────────────────
    post {
        success {
            echo """
            ============================================================
             \u2714 PIPELINE SUCCEEDED — Build #${env.BUILD_NUMBER}
             Branch : ${env.BRANCH_NAME}
            ============================================================
            """
        }
        failure {
            echo """
            ============================================================
             \u2718 PIPELINE FAILED — Build #${env.BUILD_NUMBER}
             Check Stage 3 (Quality Gate) output for test details.
             No containers were modified.
            ============================================================
            """
        }
        always {
            // Clean up virtualenv to keep the Jenkins workspace tidy
            sh 'rm -rf venv || true'
        }
    }

}
