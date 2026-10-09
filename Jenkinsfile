pipeline {
    agent any
    options { disableConcurrentBuilds(); timeout(time: 15, unit: 'MINUTES'); timestamps() }
    parameters {
        booleanParam(name: 'OFFLINE', defaultValue: true, description: 'Policy demo without OpenAI calls')
        booleanParam(name: 'CREATE_DRAFT_MR', defaultValue: false, description: 'Publish validated suggestions to GitLab; never merge')
        string(name: 'GITLAB_PROJECT_ID', defaultValue: '', description: 'GitLab mirror containing this exact source commit')
        string(name: 'GITLAB_TARGET_BRANCH', defaultValue: 'main', description: 'Human-reviewed target branch')
    }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Prepare') { steps {
            sh 'rm -f kube-linter.json kube-score.json analysis.json ai-report.json audit-report.html remediation-*.json; rm -rf ai-patches'
        } }
        stage('Security scans') {
            parallel {
                stage('kube-linter') { steps { sh 'bash scripts/run-kube-linter.sh' } }
                stage('kube-score') { steps { sh 'bash scripts/run-kube-score.sh' } }
            }
        }
        stage('Consolidate') { steps { sh 'python3 scripts/consolidate.py' } }
        stage('AI analysis') { steps { script {
            if (params.OFFLINE) { sh 'python3 scripts/ai-analysis.py --offline' }
            else { withCredentials([string(credentialsId: 'OPENAI_API_KEY', variable: 'OPENAI_API_KEY')]) {
                sh 'python3 scripts/ai-analysis.py'
            } }
        } } }
        stage('Report and audit') { steps {
            sh 'python3 scripts/generate-report.py'
            sh 'python3 scripts/workflow.py audit'
        } }
        stage('Remediation review') { steps { script {
            if (params.CREATE_DRAFT_MR && !params.OFFLINE) {
                withCredentials([string(credentialsId: 'GITLAB_API_TOKEN', variable: 'GITLAB_TOKEN')]) {
                    withEnv(["GITLAB_PROJECT_ID=${params.GITLAB_PROJECT_ID}", "GITLAB_TARGET_BRANCH=${params.GITLAB_TARGET_BRANCH}"]) {
                        sh 'python3 scripts/create-remediation-mr.py --apply'
                    }
                }
            } else { sh 'python3 scripts/create-remediation-mr.py' }
        } } }
        stage('Risk gate') { steps { sh 'python3 scripts/workflow.py gate' } }
    }
    post { always {
        archiveArtifacts artifacts: 'kube-linter.json,kube-score.json,analysis.json,ai-report.json,audit-report.html,ai-patches/**,remediation-*.json', allowEmptyArchive: true
        publishHTML(target: [allowMissing: true, alwaysLinkToLastBuild: true, keepAll: true, reportDir: '.', reportFiles: 'audit-report.html', reportName: 'Kubernetes security audit'])
    } }
}
