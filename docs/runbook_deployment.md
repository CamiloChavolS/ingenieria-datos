# Runbook de despliegue — RavenStack Pages

## Alcance y arquitectura

Este runbook opera únicamente la demo estática de `docs/`, publicada en GitHub Pages. El flujo no inicia PostgreSQL, Docker, Streamlit ni servicios cloud. El workflow `.github/workflows/deploy-pages.yml` valida el HTML y el JSON agregado, prepara el artefacto y lo publica con GitHub Actions.

- Repositorio: `CamiloChavolS/ingenieria-datos`
- Rama de producción: `main`
- URL: <https://camilochavols.github.io/ingenieria-datos/>
- Artefacto fuente: carpeta `docs/`
- Workflow: **Actions → Deploy portfolio to GitHub Pages**

## Despliegue normal

1. Regenerar los datos agregados desde el entorno local, si hubo cambios en los datos o métricas: `python src/export_static_demo.py`.
2. Revisar los cambios y confirmar que no se agreguen credenciales, CSV originales, nombres de cuentas ni comentarios.
3. Crear un commit que incluya los cambios de `docs/` y `.github/workflows/deploy-pages.yml`, y subirlo a `main`.
4. En GitHub, abrir **Actions → Deploy portfolio to GitHub Pages** y seguir la ejecución asociada al commit.
5. Confirmar que los trabajos `build` y `deploy` terminen en verde.
6. Abrir la URL pública en una ventana privada y comprobar carga de KPIs, filtros y gráficos.
7. Registrar fecha, commit y resultado en el historial de cambios del proyecto.

El primer uso del workflow requiere seleccionar **Settings → Pages → Build and deployment → Source → GitHub Actions**. Una vez seleccionado, los pushes a `main` que cambien `docs/` o el workflow despliegan la demo automáticamente; `workflow_dispatch` permite ejecutarlo manualmente desde Actions.

## Diagnóstico de fallos

| Síntoma | Revisión | Resolución |
| --- | --- | --- |
| Workflow no aparece en Actions | Revisar que `.github/workflows/deploy-pages.yml` esté en `main` y que Actions esté habilitado en el repositorio. | Subir el archivo a `main`; habilitar Actions en Settings si fue desactivado. |
| `Validate static site files` falla | Abrir el log del paso y confirmar que existen `docs/index.html` y `docs/assets/demo_data.json`, y que el JSON parsea correctamente. | Restaurar/crear los archivos válidos y volver a subir el cambio. |
| Deploy reporta permiso denegado | Revisar `Settings → Pages` y que la fuente sea **GitHub Actions**. Revisar también permisos y entorno `github-pages`. | Cambiar la fuente a GitHub Actions. Mantener `pages: write` e `id-token: write` en el job `deploy`. |
| Workflow verde, pero la URL muestra versión anterior o error | Revisar la URL de Pages en Settings, el commit desplegado en Actions y la consola/red del navegador. Confirmar que `index.html` referencia `assets/demo_data.json` con una ruta relativa. | Corregir la ruta/contenido, subir el arreglo y esperar que el nuevo workflow termine; luego recargar sin caché. |
| Push devuelve `Repository not found` | Confirmar propietario y URL del remoto con `git remote -v`; revisar la cuenta autenticada. | Usar la URL HTTPS que muestra **Code** en el repositorio correcto y volver a autenticar con permiso de escritura. |

## Recuperación y rollback

1. Identificar en **Actions** el último commit que desplegó una versión correcta.
2. Revertir el commit problemático en una nueva modificación de `main` con `git revert <SHA_DEL_COMMIT>`. No reescribir el historial con `reset`/force push en la rama pública.
3. Subir el commit de reversión (`git push origin main`).
4. Esperar la ejecución del workflow y confirmar los trabajos `build` y `deploy` en verde.
5. Verificar la página y el JSON en una ventana privada. Registrar el incidente, causa, commit revertido y resultado.

Para un fallo del workflow antes del despliegue, la versión previamente publicada normalmente sigue siendo la referencia visible: arreglar el paso fallido y volver a ejecutar el workflow no es un rollback de producción.

## Evidencia para demostrar ownership

Guardar enlaces o capturas de: workflow exitoso (commit y fecha), fallo diagnosticado, commit correctivo o de reversión, nueva ejecución exitosa y comprobación de la URL pública. No describir un fallo simulado como incidente real; indicar claramente si fue una prueba controlada.

## Límites operativos

La demo es estática y no tiene base de datos ni API. No hay alertas, monitoreo de disponibilidad ni soporte 24/7; los problemas se detectan mediante Actions o revisión manual de la URL. La operación demostrada corresponde a este sitio de portafolio, no a un sistema productivo de clientes.
