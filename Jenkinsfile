pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        BACKEND_IMAGE = 'team-task-backend'
        COMPOSE_PROJECT = 'ujian-chunin'
        HOST_PROJECT_DIR = '/home/hanmazaya/Documents/tugas-kuliah/cc/ujian-chunin'
        PUBLIC_URL = 'https://cc.fhanmazaya.my.id'
    }

    stages {
        stage('1. Checkout') {
            steps {
                echo 'Stage 1: Mengambil kode terbaru dari repositori GitHub (branch main)'
                checkout scm
                sh 'git log -1 --oneline'
            }
        }

        stage('2. Syntax Check') {
            steps {
                echo 'Stage 2: Memvalidasi sintaks Python app.py dan konfigurasi Docker Compose'
                sh '''
                    python3 -m py_compile app.py
                    docker compose config -q
                '''
            }
        }

        stage('3. Build Image') {
            steps {
                echo 'Stage 3: Membangun Docker image team-task-backend dari Dockerfile'
                sh '''
                    GIT_SHA=$(git rev-parse --short HEAD)
                    docker build -t ${BACKEND_IMAGE}:${BUILD_NUMBER} .
                    docker tag ${BACKEND_IMAGE}:${BUILD_NUMBER} ${BACKEND_IMAGE}:sha-${GIT_SHA}
                    docker tag ${BACKEND_IMAGE}:${BUILD_NUMBER} ${BACKEND_IMAGE}:latest
                    docker images ${BACKEND_IMAGE}
                '''
            }
        }

        stage('4. Automated Deployment') {
            steps {
                echo 'Stage 4: Menyinkronkan direktori Bind Mount dan menjalankan ulang stack Docker Compose'
                sh '''
                    docker stop production-api-container 2>/dev/null || true
                    docker rm production-api-container 2>/dev/null || true
                    docker run --rm -i -v ${HOST_PROJECT_DIR}:/host_dir alpine:3.20 sh -c "cat > /host_dir/index.html" < index.html
                    docker run --rm -i -v ${HOST_PROJECT_DIR}:/host_dir alpine:3.20 sh -c "cat > /host_dir/docker-compose.yml" < docker-compose.yml
                    docker run --rm -i -v ${HOST_PROJECT_DIR}:/host_dir alpine:3.20 sh -c "cat > /host_dir/app.py" < app.py
                    FRONTEND_DIR_PATH=${HOST_PROJECT_DIR} docker compose -p ${COMPOSE_PROJECT} up -d --force-recreate
                '''
            }
        }

        stage('5. Health Check') {
            steps {
                echo 'Stage 5: Memverifikasi kesehatan layanan Backend, Frontend, dan DNS app-net'
                sh '''
                    sleep 3
                    curl -fsS http://localhost:5000/health
                    echo ""
                    curl -fsS http://localhost:5000/tasks | head -c 320
                    echo ""
                    curl -fsS -I http://localhost:3000/ | head -n 5
                    docker exec team-task-frontend wget -qO- http://backend:5000/health
                    echo ""
                    docker compose -p ${COMPOSE_PROJECT} ps
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline CI/CD Ujian Chunin selesai dengan status SUCCESS.'
        }
        failure {
            echo 'Pipeline CI/CD gagal. Periksa Console Output untuk rincian tahap yang gagal.'
        }
    }
}
