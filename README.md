# MEDTRAIL — Sistema Integrado de Saúde e Longevidade
MVP técnico para upload e gestão documental, dashboard e 6 módulos MEDTRAIL.

Módulos: BODY TRAIL; CLINIC TRAIL; FARMOTRAIL | FARMATECNOLOGIA; SOCIAL & LIFESTYLE; LIFE RISK PREVISION; MEDTRAIL AI.

## Executar localmente
```bash
docker compose up --build
```

A aplicação fica em `http://localhost:8000` e a documentação em `http://localhost:8000/docs`.
As credenciais locais são `admin@medtrail.local / ChangeMe123!`. Altere-as antes de usar dados reais.

## Deploy com GitHub + Render
1. Crie um repositório GitHub e envie **todo o conteúdo desta pasta**, incluindo `backend/`, `frontend/`, `render.yaml` e `docker-compose.yml`.
2. No Render, selecione **New > Blueprint** e conecte o repositório GitHub.
3. Escolha o branch que contém `render.yaml` e aplique o Blueprint. O Render criará o serviço Docker e o PostgreSQL.
4. Aguarde o health check `/health` ficar verde. O serviço usa automaticamente a porta `PORT` fornecida pelo Render.
5. Abra a URL pública do serviço e altere `DEMO_EMAIL` e `DEMO_PASSWORD` nas variáveis do Render. Faça um novo deploy depois de alterar secrets.

O Render Blueprint usa PostgreSQL gerido, gera `JWT_SECRET` e `DEMO_PASSWORD`, e grava uploads em `/tmp/medtrail-storage`. Esse armazenamento é efêmero: para retenção clínica real, substitua-o por object storage privado com backup, antivírus e política de retenção.

### Variáveis de produção
- `DATABASE_URL`: criada automaticamente pelo PostgreSQL do Render.
- `JWT_SECRET`: gerada pelo Render; nunca a versionar no GitHub.
- `DEMO_EMAIL` e `DEMO_PASSWORD`: credenciais iniciais; substitua por autenticação administrativa real antes de produção.
- `STORAGE_DIR`: `/tmp/medtrail-storage` no Blueprint atual.
- `MAX_FILE_SIZE_MB`: limite de upload, por padrão `20`.

Upload permitido: PDF, PNG, JPG/JPEG, DOCX, XLSX; limite 20 MB; nomes internos UUID; validação de assinatura/MIME; armazenamento fora do webroot; autenticação e auditoria.

Antes de produção: HTTPS, PostgreSQL gerido, object storage privado, antivirus/sandbox, backups/DR, MFA/RBAC, gestão de consentimento, retenção, testes de segurança e validação clínica/regulatória.

A IA desta versão é apenas estrutura de apoio; não diagnostica nem altera medicamentos automaticamente.
