def changedFiles = []

pipeline {
    agent any

    environment {
        // Clé API OpenAI pour l'analyse IA
        OPENAI_API_KEY     = credentials('OPENAI_API_KEY')
        // ID de votre projet GitLab
        GITLAB_PROJECT_ID  = '84021173'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Detect changed files') {
            steps {
                script {
                    // Supprimer les anciens rapports du workspace pour éviter les conflits de mémoire
                    sh 'rm -f kube-linter.json kube-score.json renovate.json analysis.json ai-report.json audit-report.html'
                    sh 'rm -rf ai-patches/'

                    // Utilisation de GIT_PREVIOUS_SUCCESSFUL_COMMIT (Correction #4)
                    def prevCommit = env.GIT_PREVIOUS_SUCCESSFUL_COMMIT ?: sh(
                        script: 'git rev-parse HEAD~1 2>/dev/null || echo ""',
                        returnStdout: true
                    ).trim()

                    def diffCmd = prevCommit
                        ? "git diff --name-only ${prevCommit} HEAD -- k8s/"
                        : "git ls-tree -r --name-only HEAD -- k8s/"

                    def changed = sh(
                        script: "${diffCmd} | grep -E '\\.(yaml|yml)\$' || true",
                        returnStdout: true
                    ).trim()

                    if (!changed) {
                        echo "ℹ️ Aucun fichier Kubernetes modifié dans ce commit — saut des étapes de scan."
                        env.CHANGED_FILES = ''
                        env.NO_CHANGES = 'true'
                    } else {
                        echo "🔍 Fichiers Kubernetes modifiés détectés :\n${changed}"
                        env.CHANGED_FILES = changed.split('\n').join(' ')
                        env.NO_CHANGES = 'false'
                    }
                }
            }
        }

        stage('Security Scans') {
            when { expression { env.NO_CHANGES == 'false' } }
            // Parallélisation des outils de scan (Correction #5)
            parallel {
                stage('kube-linter') {
                    steps {
                        sh 'bash scripts/run-kube-linter.sh $CHANGED_FILES'
                    }
                }
                stage('kube-score') {
                    steps {
                        sh 'bash scripts/run-kube-score.sh $CHANGED_FILES'
                    }
                }
            }
        }

        stage('Renovate') {
            steps {
                // Simulation requise par consolidate.py
                sh 'echo "[]" > renovate.json'
            }
        }

        stage('Consolidate') {
            when { expression { env.NO_CHANGES == 'false' } }
            steps {
                sh 'python3 scripts/consolidate.py --files $CHANGED_FILES'
            }
        }

        stage('AI Analysis') {
            when { expression { env.NO_CHANGES == 'false' } }
            steps {
                sh 'python3 scripts/ai-analysis.py'
            }
        }

        stage('Generate Report') {
            when { expression { env.NO_CHANGES == 'false' } }
            steps {
                sh 'python3 scripts/generate-report.py'
            }
        }

        stage('Auto-Remediation MR') {
            when {
                expression { env.NO_CHANGES == 'false' }
                expression {
                    // Vérifier si l'IA a généré des correctifs (patches)
                    def report = readJSON file: 'ai-report.json'
                    return report.patches != null && report.patches.size() > 0
                }
            }
            steps {
                // Injecter le token GitLab requis pour appeler l'API de GitLab et pousser la MR
                withCredentials([string(credentialsId: 'GITLAB_API_TOKEN', variable: 'GITLAB_TOKEN')]) {
                    sh """
                        GITLAB_TOKEN=${GITLAB_TOKEN} \
                        GITLAB_PROJECT_ID=${GITLAB_PROJECT_ID} \
                        BUILD_NUMBER=${env.BUILD_NUMBER} \
                        GIT_BRANCH=${env.GIT_BRANCH} \
                        python3 scripts/create-remediation-mr.py
                    """
                }
            }
        }

        stage('Check Risk') {
            when { expression { env.NO_CHANGES == 'false' } }
            steps {
                script {
                    // Utilisation de readJSON pour le parsing propre (Correction #6)
                    def report = readJSON file: 'ai-report.json'
                    if (report.criticite == 'HIGH') {
                        error("❌ DÉPLOIEMENT BLOQUÉ : Risque critique détecté par l'IA — consultez Rapport DevSecOps.")
                    }
                }
            }
        }
    }

    post {
        always {
            // Archiver les rapports générés
            archiveArtifacts(
                artifacts: 'kube-linter.json,kube-score.json,renovate.json,analysis.json,ai-report.json,audit-report.html',
                allowEmptyArchive: true
            )
            // Publication du rapport HTML
            publishHTML(target: [
                allowMissing        : true,
                alwaysLinkToLastBuild: true,
                keepAll             : true,
                reportDir           : '.',
                reportFiles         : 'audit-report.html',
                reportName          : 'Rapport DevSecOps'
            ])
        }
        failure {
            // Bloc d'envoi d'e-mail d'alerte en cas d'échec (Correction #7)
            mail to: 'haythemgarbaa15@gmail.com',
                 subject: "❌ Pipeline DevSecOps FAILED — ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "L'analyse a détecté un problème critique. Consultez le rapport : ${env.BUILD_URL}"
        }
    }
}
