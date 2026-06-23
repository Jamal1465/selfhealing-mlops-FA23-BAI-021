pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')

        DOCKERHUB_USER = 'jamal1465'
        IMAGE_UNSTABLE = "${DOCKERHUB_USER}/sentiment-api:unstable"
        IMAGE_STABLE   = "${DOCKERHUB_USER}/sentiment-api:stable"

        APP_CONTAINER = "sentiment-app-test"
        APP_PORT = "5100"

        KUBECONFIG = "/var/lib/jenkins/.kube/config"
    }

    stages {

        stage('Fetch') {
            steps {
                cleanWs()
                checkout scm

                sh '''
                    echo "Current commit:"
                    git log --oneline -1

                    echo "Checking that main app.py is unstable..."
                    grep -n "unstable-v1" app.py

                    echo "Workspace files:"
                    ls -la
                '''
            }
        }

        stage('Build and Run') {
            steps {
                sh '''
                    docker rm -f ${APP_CONTAINER} || true

                    echo "Building unstable image from main branch..."
                    docker build --no-cache -t ${IMAGE_UNSTABLE} .

                    echo "Running unstable app on host port ${APP_PORT}..."
                    docker run -d --name ${APP_CONTAINER} -p ${APP_PORT}:5000 ${IMAGE_UNSTABLE}

                    echo "Waiting for unstable app..."
                    for i in $(seq 1 300); do
                        RESPONSE=$(curl -s http://localhost:${APP_PORT}/health || true)
                        echo "$RESPONSE"

                        echo "$RESPONSE" | grep "unstable-v1" && echo "Unstable app is ready!" && exit 0

                        echo "Waiting... ($i/300)"
                        sleep 2
                    done

                    echo "ERROR: App did not become ready as unstable-v1"
                    docker ps -a --filter "name=${APP_CONTAINER}"
                    docker logs ${APP_CONTAINER} --tail=150
                    exit 1
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    echo "Running API tests against http://localhost:${APP_PORT}"

                    docker run --rm --network host \
                      -e BASE_URL=http://localhost:${APP_PORT} \
                      ${IMAGE_UNSTABLE} \
                      bash -c "pytest tests/test_api.py -v --tb=short"
                '''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
                    echo "Running Selenium UI test against http://localhost:${APP_PORT}"

                    docker run --rm --network host \
                      -v $(pwd)/tests:/tests \
                      -e BASE_URL=http://localhost:${APP_PORT} \
                      --shm-size=2g \
                      selenium/standalone-chrome:latest \
                      bash -lc "python3 -m pip install selenium pytest requests -q && pytest /tests/test_ui.py -v --tb=short"
                '''
            }
        }

        stage('Build and Push') {
            steps {
                sh '''
                    echo "Logging in to DockerHub..."
                    echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin

                    echo "Pushing unstable image..."
                    docker push ${IMAGE_UNSTABLE}

                    echo "Fetching stable-fallback branch..."
                    git fetch origin stable-fallback

                    echo "Taking stable app.py from stable-fallback branch..."
                    git checkout origin/stable-fallback -- app.py

                    echo "Checking stable app.py..."
                    grep -n "stable-v0" app.py

                    echo "Building stable image..."
                    docker build --no-cache -t ${IMAGE_STABLE} .

                    echo "Pushing stable image..."
                    docker push ${IMAGE_STABLE}

                    echo "Restoring main branch app.py from current HEAD..."
                    git checkout HEAD -- app.py

                    echo "Checking restored main app.py..."
                    grep -n "unstable-v1" app.py
                '''
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    export KUBECONFIG=/var/lib/jenkins/.kube/config

                    echo "Checking kubectl access..."
                    kubectl get nodes

                    echo "Applying Kubernetes files..."
                    kubectl apply -f k8s/pvc.yaml
                    kubectl apply -f k8s/blue-deployment.yaml
                    kubectl apply -f k8s/green-deployment.yaml
                    kubectl apply -f k8s/service.yaml

                    echo "Waiting for blue deployment..."
                    kubectl rollout status deployment/sentiment-blue-deployment --timeout=180s

                    echo "Waiting for green deployment..."
                    kubectl rollout status deployment/sentiment-green-deployment --timeout=180s

                    echo "Pods:"
                    kubectl get pods -o wide

                    echo "Service:"
                    kubectl get svc sentiment-api-service
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

        success {
            echo "Pipeline completed successfully."
        }

        failure {
            echo "Pipeline failed. Check logs above."
        }
    }
}
