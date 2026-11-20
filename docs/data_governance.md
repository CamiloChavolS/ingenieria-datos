# Gobierno y controles de acceso

## Alcance

El dataset de demostración es sintético y no representa tratamiento de datos personales reales. Esta documentación describe controles técnicos y una base de diseño para GDPR/LGPD; no acredita cumplimiento ni reemplaza asesoría legal, una evaluación de impacto, contratos con encargados o decisiones del responsable del tratamiento.

## Inventario y propósito

| Capa o dato | Uso del proyecto | Clasificación de demostración | Control aplicado |
|---|---|---|---|
| Bronze: cuentas, suscripciones, uso, soporte y churn | Conservar los archivos fuente y reconstruir transformaciones | Datos sintéticos de origen | Dataset BigQuery `bronze`; permisos de escritura solo para pipeline |
| Silver: hechos consolidados por cliente | Limpieza, joins y variables para analítica/ML | Identificadores de cuenta | Acceso de pipeline; transformaciones dbt |
| Gold: dimensiones, hecho y marts | Dashboard, KPIs y análisis segmentado | `account_id` y `account_name` restringidos | Policy tags en dimensión/hecho/mart; política de filas por país en tablas físicas |
| Comentarios de churn enviados a Gemini | Etiquetar tema y sentimiento | Texto libre potencialmente identificable en otros contextos | Límite por registro/caracteres, enmascarado de correo/teléfono/URL y ejecución manual |
| Artefacto del modelo | Inferencia del dashboard | Modelo serializado no público | Bucket privado; pipeline crea, runtime solo lee |

## Identidades y permisos

- **Pipeline:** identidad federada desde GitLab; ingiere Bronze, ejecuta dbt, entrena el modelo y usa Vertex AI. Tiene permisos de escritura en Bronze/Silver y acceso Data Owner en Gold para materializar dimensiones, hechos y marts, administrar policy tags y recibir acceso completo a filas para las tareas de proceso.
- **Despliegue:** identidad federada distinta; publica imágenes y despliega Cloud Run, sin permisos de consulta de los datasets ni de Vertex AI.
- **Runtime:** cuenta de servicio de Cloud Run; consulta Gold con scope de filas configurado en las tablas físicas y lee artefactos desde el bucket privado. La consulta de la aplicación omite `account_id` y `account_name`.
- **Analistas:** grupo de Google configurable; lectura de Gold y filas del país de demostración. No recibe acceso a las columnas identificadoras por defecto; Fine-Grained Reader debe aprobarse y concederse aparte si un caso de uso lo requiere.

Workload Identity Federation limita la confianza al proyecto GitLab y la rama protegida configurados; no se guardan llaves JSON estáticas. El job de publicación GitHub usa un token protegido/enmascarado y hace push fast-forward de la rama principal, sin `--mirror` ni force push.

## Salvaguardas y controles pendientes para producción

La política `US` es solo una muestra técnica de segmentación y corresponde a un país presente en el snapshot sintético actual. Antes de usar datos reales, el responsable del tratamiento debe definir base jurídica y finalidad, minimizar campos y texto, acordar residencia/región, cifrado y retención, habilitar auditoría y revisión periódica de accesos, implementar solicitudes de acceso/corrección/supresión, gestionar incidentes y evaluar riesgos/impacto. Las regex de correo, teléfono y URL reducen exposición frecuente, pero no detectan nombres, identificadores indirectos ni toda información sensible; no se deben enviar datos personales reales a Gemini con esta configuración de demostración sin autorización, evaluación y controles organizacionales apropiados.

Los outputs de IA requieren muestreo y aprobación humana antes de decisiones de retención. El score de churn del dataset actual es exploratorio y no es una decisión automatizada.
