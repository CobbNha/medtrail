# MEDTRAIL — Sistema Integrado de Saúde e Longevidade
MVP técnico para upload e gestão documental, dashboard e 6 módulos MEDTRAIL.

Módulos: BODY TRAIL; CLINIC TRAIL; FARMOTRAIL | FARMATECNOLOGIA; SOCIAL & LIFESTYLE; LIFE RISK PREVISION; MEDTRAIL AI.

## Executar
docker compose up --build
Frontend/API: http://localhost:8000
Docs API: http://localhost:8000/docs

Demo: admin@medtrail.local / ChangeMe123!
ALTERE A PASSWORD E JWT_SECRET ANTES DE USAR DADOS REAIS.

Upload permitido: PDF, PNG, JPG/JPEG, DOCX, XLSX; limite 20 MB; nomes internos UUID; validação de assinatura/MIME; armazenamento fora do webroot; autenticação e auditoria.

Antes de produção: HTTPS, PostgreSQL gerido, object storage privado, antivirus/sandbox, backups/DR, MFA/RBAC, gestão de consentimento, retenção, testes de segurança e validação clínica/regulatória.

A IA desta versão é apenas estrutura de apoio; não diagnostica nem altera medicamentos automaticamente.
