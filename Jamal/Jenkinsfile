pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')
        DOCKERHUB_USER = 'bilalaskari'
        IMAGE_UNSTABLE = "${DOCKERHUB_USER}/sentiment-api:unstable"
        IMAGE_STABLE   = "${DOCKERHUB_USER}/sentiment-api:stable"
        APP_CONTAINER  = "sentiment-app-test"
        APP_PORT       = "5000"
    }

    stages {
        stage('Fetch') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run') {
            steps {
                sh '''
                    # Clean up previous container
                    docker rm -f ${APP_CONTAINER} || true

                    # Build unstable image
                    docker build -t ${IMAGE_UNSTABLE} .

                    # Run container with host network
                    docker run -d --name ${APP_CONTAINER} \
                        --network host \
                        ${IMAGE_UNSTABLE}

                    # Health check instead of fixed sleep
                    for i in $(seq 1 30); do
                        if curl -sf http://localhost:${APP_PORT}/health; then
                            echo "App is ready!"
                            break
                        fi
                        echo "Waiting for app to start... (${i}/30)"
                        sleep 1
                    done
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    docker run --rm \
                        --network host \
                        -e BASE_URL=http://localhost:${APP_PORT} \
                        ${IMAGE_UNSTABLE} \
                        bash -c "pytest tests/test_api.py -v --tb=short"
                '''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
                    docker run --rm \
                        --network host \
                        -v $(pwd)/tests:/tests \
                        -e APP_URL=http://localhost:${APP_PORT} \
                        --shm-size=2g \
                        selenium/standalone-chrome:latest \
                        bash -c "pip install selenium pytest requests -q && pytest tests/test_ui.py -v --tb=short"
                '''
            }
        }

        stage('Build and Push') {
            steps {
                sh '''
                    echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin

                    # Push unstable image
                    docker push ${IMAGE_UNSTABLE}

                    # Save main branch files
                    cp app.py /tmp/app-main.py
                    cp requirements.txt /tmp/requirements-main.txt
                    cp Dockerfile /tmp/Dockerfile-main

                    # Get all stable-fallback files (lightweight Dockerfile + requirements.txt + app.py)
                    git fetch origin stable-fallback
                    git checkout origin/stable-fallback -- app.py requirements.txt Dockerfile

                    # Build lightweight stable image (~150MB, not 8GB)
                    docker build -t ${IMAGE_STABLE} .
                    docker push ${IMAGE_STABLE}

                    # Restore main branch files
                    cp /tmp/app-main.py app.py
                    cp /tmp/requirements-main.txt requirements.txt
                    cp /tmp/Dockerfile-main Dockerfile
                '''
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    export KUBECONFIG=/var/lib/jenkins/.kube/config

                    # Apply configurations
                    kubectl apply -f k8s/pvc.yaml
                    kubectl apply -f k8s/blue-deployment.yaml
                    kubectl apply -f k8s/green-deployment.yaml
                    kubectl apply -f k8s/service.yaml

                    # Wait for blue deployment
                    kubectl rollout status deployment/sentiment-blue-deployment --timeout=120s
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f ${APP_CONTAINER} || true
                docker logout || true
            '''
        }
    }
}
