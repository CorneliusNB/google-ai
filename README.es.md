# ePlus AI Toolkit — Español

<!-- Source README.md git-blob: 66dc72117e92b338bad604c5fd83517588cf878a -->

[English](README.md) · [Tiếng Việt](README.vi.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Español** · [Français](README.fr.md)

**Vista previa de macOS:** la [versión para Mac](docs/MACOS-PREVIEW.md) implementa los pasos 0–5. Los pasos de pago 2–5 pueden generar cargos reales y requieren confirmación individual; el funcionamiento real con Mac/MuMu aún no se ha verificado.

> **Referencia principal:** [README en inglés](README.md). Esta traducción explica el uso esencial y los riesgos; si hay diferencias, consulta el código actual y la documentación inglesa.

**ePlus AI Toolkit** es una herramienta de terminal para **Windows y macOS** que usa **PowerShell (solo en Windows) o Terminal (zsh/bash, en macOS)**, además de Python, ADB, Frida y un dispositivo/emulador Android compatible para consultar ofertas de Google AI Pro mediante Google One y Google Play. La interfaz Textual y el CLI usan el mismo motor.

![Interfaz de ePlus AI Toolkit](https://github.com/user-attachments/assets/f16cde7e-022f-43bc-97fe-310012b0a5d3)

> [!CAUTION]
> **Proyecto no oficial; pueden producirse cargos reales.** Los **pasos 2–5** pueden abrir un proceso de pago real de Google Play y pulsar **Subscribe** automáticamente. Encontrar una oferta, ver un precio inicial de cero o recibir un mensaje de envío del pago **no demuestra** que la cuenta cumpla los requisitos, que la suscripción sea gratuita, que esté activa ni que se haya ampliado. Antes de cada pago, comprueba en Google Play la cuenta, el importe de hoy, el precio de renovación y la siguiente fecha de cobro. Detener el programa no deshace una transacción enviada.

> [!NOTE]
> **La verificación de la tarjeta puede retener fondos temporalmente aunque Google Play muestre un total de 0 USD.** Podrías ver una **preautorización pendiente de unos 3 USD** (o de otro importe). **Los 3 USD son un ejemplo, no una tarifa fija de Google ni un cargo de suscripción confirmado.** La retención puede reducir temporalmente el saldo disponible. Según Google, las autorizaciones no son compras y normalmente se liberan en **1–14 días laborables**, según el banco. Si el importe se contabiliza como cargo definitivo o sigue retenido pasados 14 días laborables, contacta con tu banco y Google Payments. [Información oficial de Google Play](https://support.google.com/googleplay/answer/6224192?hl=en).

## Descargo de responsabilidad

Este proyecto es **independiente y no está afiliado, patrocinado ni respaldado** por Google, Google One, Google Play, NetEase o MuMuPlayer. El software se ofrece **tal cual**, sin garantías de elegibilidad, resultado de suscripción o compatibilidad. Úsalo solo con cuentas y dispositivos propios o autorizados y respeta las leyes y condiciones de cada plataforma. Lee el [descargo completo (inglés)](DISCLAIMER.md) y las [precauciones de seguridad](SECURITY.md).

## 1. Requisitos e instalación de MuMuPlayer

**Elige las instrucciones de tu sistema operativo.** Windows usa PowerShell; macOS usa Terminal (zsh/bash), **sin PowerShell**.

| Software / configuración | Windows | macOS |
| --- | --- | --- |
| Terminal | **PowerShell 5.1+** | **Terminal**, zsh/bash |
| Python | **3.10+**, comando `python` | **3.10+**, `python3`; se crea `.venv` local |
| Git | Git para Windows | Git mediante Xcode Command Line Tools o Homebrew |
| Android | Dispositivo con root/ADB; flujo compatible con MuMuPlayer para Windows | Android con root o emulador compatible; MuMuPlayer Pro para Mac es opción en **Apple Silicon**, no en Intel |
| Aplicaciones | Google Play Store y Google One con la cuenta correcta | Las mismas aplicaciones en el Android elegido |
| ADB | El iniciador puede buscar/descargar Platform-Tools | Instalar por separado, p. ej. `brew install android-platform-tools`; comprobar `adb devices` |
| Frida | **16.5.9**, preparada por el asistente Windows | **16.5.9** en `.venv`; verificar compatibilidad Android |
| Inicio | `.\run-all.ps1` | `sh run-macos.sh` o `ePlus-AI-Toolkit.command` |

Ambos sistemas requieren un entorno Android autorizado y configurado correctamente. El código macOS cubre Steps 0–5, pero **no hay comprobación real de pagos en Mac/MuMu**. Consulta las guías de [Windows](docs/INSTALLATION.md) y [macOS](docs/MACOS-PREVIEW.md).


- **Windows**, PowerShell **5.1+** y Python **3.10+**.
- **Instala MuMuPlayer por separado**, inicia Android con root y depuración ADB habilitados.
- Instala e inicia sesión en **Google Play Store** y **Google One** dentro del emulador.
- La herramienta puede localizar/descargar **Android SDK Platform-Tools (ADB)** y preparar **Frida 16.5.9**, pero **no descarga ni instala MuMuPlayer**. La compatibilidad de Frida depende de la versión de Android.

**Descarga oficial de MuMuPlayer:** [mumuplayer.com/download](https://www.mumuplayer.com/download/) (elige Windows). Evita sitios de terceros. Consulta la [guía de instalación de la Wiki](https://github.com/hoangsvit/google-ai/wiki/Install).

## 2. Descargar y ejecutar

En PowerShell:

```powershell
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
.\run-all.ps1
```

Si ya clonaste el repositorio:

```powershell
git pull --ff-only
.\run-all.ps1
```

Al ejecutar **sin parámetros** se abre el panel Textual; no se inicia una compra automáticamente. Cuando sea necesario, el programa puede preparar Textual, ADB o Frida. Normalmente **no hace falta** ejecutar `setup_env.py` antes. La preparación puede modificar el emulador, el proxy o la configuración de red.

Si ADB está disponible en PATH, comprueba la conexión:

```powershell
adb devices
```

El estado debe ser `device`, no `offline` ni `unauthorized`. Más información en la [guía técnica](docs/DETAILED-GUIDE.md).

### Alternativa: usar una versión publicada si falla el código más reciente

Si la versión actual del repositorio da errores, puedes probar una **versión publicada anteriormente** desde [GitHub Releases](https://github.com/hoangsvit/google-ai/releases). Lee las notas y descarga el paquete de Windows **si está adjunto**. Si únicamente aparece el archivo automático **Source code (zip)** de GitHub, descárgalo, descomprímelo, abre PowerShell en la carpeta extraída y ejecuta:

```powershell
.\run-all.ps1
```

**Source code (zip) no es un `.exe` precompilado ni un instalador.** Guarda la versión publicada en **otra carpeta**, sin sobrescribir tu copia actual. Una versión anterior puede no contener las correcciones más recientes; siguen siendo necesarios Windows, Python, MuMuPlayer, ADB/Frida y las mismas precauciones sobre pagos. Si el problema continúa, consulta la [guía de solución de problemas](docs/DETAILED-GUIDE.md) o [abre una incidencia](https://github.com/hoangsvit/google-ai/issues).

## macOS — Instalación y ejecución

En macOS, instala **Git**, **Python 3.10+** y **Android SDK Platform-Tools (ADB)** (Homebrew: `brew install android-platform-tools`). Conecta un dispositivo Android con root, Google Play Store y Google One, o un emulador compatible. **MuMuPlayer Pro para Mac requiere Apple Silicon**; en Intel se necesita otro entorno Android compatible.

Abre **Terminal** y ejecuta:

```sh
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
adb devices
sh run-macos.sh
```

`sh run-macos.sh` abre el panel Textual con **pasos 0–5**. `--check` revisa el entorno (puede modificar ajustes), `--list` solo consulta ofertas y `--step 2` solo selecciona el paso, **sin pagar automáticamente**. Los pasos 2–5 pueden generar cargos reales y requieren aprobación individual. **Los pagos en un Mac/MuMu real aún no se han verificado.** Consulta la [guía Mac completa](docs/MACOS-PREVIEW.md).

## Diagnóstico de conexión y Offer Explorer (Windows + macOS)

El panel incluye dos acciones centradas en la **inspección**, adaptadas de la configuración Android y del listado de ofertas del proyecto original:

- **Diagnose Android connection:** busca ADB existente, enumera dispositivos Android autorizados, obtiene la arquitectura ABI, verifica Google One e informa de la versión de Frida del equipo. En Windows ofrece instrucciones para PowerShell/MuMu/Platform-Tools; en macOS para Terminal/zsh/bash y Homebrew. **No instala programas, conecta ni reinicia el emulador, inicia Frida ni realiza pagos.** La orden `adb devices` puede iniciar el servidor ADB local.
- **Check Device & Offers (Step 1):** usa el flujo Android/Frida y muestra **Offer Explorer** debajo de Live Status: únicamente ID de producto, ID de oferta, primer período de facturación y si el precio inicial es cero o distinto de cero. **No muestra** tokens de ofertas/compras, identificadores completos de cuenta ni datos de tarjetas. La consulta puede configurar Android; **no está libre de efectos secundarios**.

Un precio inicial de cero **no confirma** elegibilidad, activación, renovación ni precios futuros. Step 1 consulta en modo lista solo `g1.2tb.ai.subs_variant`, `g1.play.2tb.ai` y `g1.2tb.ai`; Steps 2–5 conservan sus consultas específicas. Como el informe Android no contiene todos los períodos posteriores, Offer Explorer marca sus precios como **no verificados**. Comprueba siempre las condiciones y los cargos en Google Play.

## 3. Usar el panel Textual

En una ejecución, los botones Check Device & Offers, Run y los selectores de modo/paso quedan bloqueados. Step 0 puede modificar el entorno local; Step 1 no compra, pero su preflight puede preparar ADB/Frida. Una acción Next solo se permite tras un resultado verificable en Google Play. **Exit/Stop no revierte una compra ya enviada.**


**Check Device & Offers** ejecuta **Step 1 — Available offers**: consulta ofertas y **no inicia el pago**. Supervisa **Live Status** y **Show technical details**; 30 segundos sin nuevos mensajes no implican necesariamente un bloqueo.

En **Advanced: Run by step**:

| Modo | Acción |
| --- | --- |
| **One step only** | Ejecuta un único paso seleccionado, del 0 al 5 |
| **From selected step** | Inicia una secuencia guiada desde el paso 2–5 |
| **All: Steps 2–5** | Inicia la secuencia desde el paso 2; el 5 es opcional |

| Paso | Función | Riesgo |
| --- | --- | --- |
| **0 — Environment** | Diagnóstico/preparación de Android, ADB y Frida | Sin compra; puede cambiar ajustes locales |
| **1 — Available offers** | Consulta de ofertas de Google Play | Sin compra; la preparación puede cambiar ajustes |
| **2 — Pro 12 months** | Oferta original de 12 meses | **Posible cargo real** |
| **3 — Pro +6 months** | Actualización de suscripción original | **Posible cargo real** |
| **4 — Pro +6 months (second)** | Segunda actualización de suscripción | **Posible cargo real** |
| **5 — Optional +6 months** | Actualización adicional opcional | **Posible cargo real** |

Los meses son **nombres históricos de los pasos**, no una garantía de ampliación. Si ya tienes una suscripción activa, **no repitas el paso 2**.

El TUI exige **aprobación explícita por cada paso de pago**. Aunque aparezca un mensaje de pago enviado, comprueba el estado real, los cargos y la renovación en [Suscripciones de Google Play](https://play.google.com/store/account/subscriptions). Pulsa **Verified in Google Play → Next** solo si has confirmado personalmente el cambio. La herramienta **no puede demostrar por sí misma** la activación.

**Detener/salir:** Stop en los pasos 0–1 solicita cancelar el proceso local. En los pasos 2–5, **Stop after this step** evita los pasos siguientes, pero **no fuerza la interrupción de un pago en curso**. **Q / Exit** espera a que acabe el paso de pago actual. **D** alterna los detalles; **R** inicia el modo seleccionado.

## 4. PowerShell CLI (avanzado)

**Consulta y diagnóstico, sin pago:**

```powershell
.\run-all.ps1 -Step 1
.\run-all.ps1 -Step 1 -Debug
.\run-all.ps1 -Step 0
.\run-all.ps1 -Cli
```

**Los siguientes comandos pueden iniciar pagos reales:**

```powershell
.\run-all.ps1 -Step 2
.\run-all.ps1 -Step 3
.\run-all.ps1 -Step 4
.\run-all.ps1 -Step 5
```

A diferencia del TUI, un comando individual `-Step 2..5` **no pide una segunda aprobación escrita en PowerShell**. Ejecútalo solo si realmente deseas intentar una compra y ya comprobaste las condiciones.

Secuencia guiada del CLI:

```powershell
.\run-all.ps1 -AllStages
.\run-all.ps1 -AllStages -StartStep 3
```

Confirmaciones: **1 = Continue (continuar), 2 = End run (terminar), 0 = Stop (detener)**. Comprueba Google Play antes de pasar al paso siguiente. `-StartStep 3` no demuestra que las ampliaciones anteriores hayan funcionado.

Parámetros opcionales:

```powershell
.\run-all.ps1 -Step 1 -Serial emulator-5554
.\run-all.ps1 -AllStages -Email "account@gmail.com"
```

Usa solo un número de serie mostrado por ADB. Evita `-Force`: omite la comprobación de la cuenta, **pero no modifica** la elegibilidad ni las restricciones de pago de Google.

## 5. Problemas habituales y resultados

- **MuMu/ADB no detectado:** revisa el emulador, root, ADB y los permisos del dispositivo.
- **Error de Frida:** revisa los detalles y la compatibilidad de **16.5.9** con Android.
- **Sin ofertas:** abre Google One/Play Store y vuelve a ejecutar **Step 1**.
- **Cuenta incorrecta:** verifica el perfil de Google Play; no omitas la comprobación.
- **Pago solicitado:** no confirma una suscripción nueva ni una renovación; revisa Google Play antes de repetirlo.
- **Error de seguridad de pagos (por ejemplo OR-REH-04):** detén los pasos de pago y sigue el procedimiento oficial.

Los registros están en `logs/` y los informes en `ultra0-report/`. **No compartas archivos sin ocultar correos, tokens y datos de pago.** CI solo ejecuta pruebas estáticas/simuladas y **no valida compras reales**. 
## Soporte comunitario y proyectos relacionados

Si tienes problemas para instalar o utilizar ePlus AI Toolkit, puedes contactar e intercambiar consejos con la comunidad en la [publicación de soporte y debate de ePlus en Telegram](https://t.me/eplus_news/29). Para errores reproducibles, también puedes [abrir un Issue en GitHub](https://github.com/hoangsvit/google-ai/issues). **No compartas contraseñas, códigos OTP/2FA, tokens de ofertas o compras, registros sin anonimizar ni datos de tarjetas.** No es un canal de soporte oficial de Google.

**¿No puedes acceder a la oferta de Google AI Pro?** Puedes conocer otro proyecto comunitario de ePlus.DEV: [Muse Invite Hub](https://github.com/ePlus-DEV/muse-invite-hub), donde es posible [buscar o compartir códigos de invitación de Muse](https://muse.eplus.dev/). **Muse es un servicio distinto**: sus códigos **no activan ni sustituyen** una suscripción a Google AI Pro. La disponibilidad de los códigos y los requisitos de acceso pueden variar.

## Estructura del repositorio

Los iniciadores y módulos Python activos se mantienen en la raíz para conservar la compatibilidad. Usa `run-all.ps1` en Windows o `run-macos.sh` en macOS.

| Ubicación | Función |
| --- | --- |
| `run-all.ps1` | Entrada Windows: panel Textual y CLI guiado |
| `run-macos.sh`, `ePlus-AI-Toolkit.command`, `macos_runner.py` | Iniciador/adaptador macOS, Steps 0–5; pagos reales sin verificar |
| `tui.py`, `tui_core.py`, `ultra0.py`, `setup_env.py`, `device_selector.py`, `query_sku.py` | Motor Python y utilidades activas |
| [`tools/windows/`](tools/windows/README.md) | Configuración manual opcional de Windows |
| [`legacy/windows/`](legacy/windows/README.md) | Accesos directos antiguos; algunos usan `--force` y pueden generar **cargos reales** |
| `scripts/`, `assets/` | Ayudantes y recursos Android/Frida |
| `tests/`, `.github/workflows/`, `docs/` | Pruebas sin conexión, CI y documentación |

## Documentación y créditos

[README en inglés](README.md) · [Wiki de instalación](https://github.com/hoangsvit/google-ai/wiki/Install) · [Guía detallada](docs/DETAILED-GUIDE.md) · [Pasos originales](docs/ORIGINAL-STEPS.md) · [Descargo](DISCLAIMER.md) · [Seguridad](SECURITY.md) · [Contribuir](CONTRIBUTING.md) · [Avisos de terceros](THIRD_PARTY_NOTICES.md)

La documentación incluye [estructura del proyecto](docs/PROJECT.md), [uso del panel y CLI](docs/USAGE.md), [seguridad de facturación](docs/SAFETY.md), [notas del autor](docs/AUTHOR-NOTES.md) y [normas para agentes](AGENTS.md). GitHub Actions prueba Python, PowerShell, Textual y Frida/Billing mediante simulaciones, **sin transacciones reales**. Aprobar CI no acredita compatibilidad física ni elegibilidad.

## Créditos**Autor original:** [@gylive](https://github.com/gylive) — [google-ultra](https://github.com/gylive/google-ultra). **Mantenedor:** [David Nguyen (@hoangsvit)](https://github.com/hoangsvit) / [ePlus.DEV](https://eplus.dev). El aviso MIT del autor original permanece en `THIRD_PARTY_NOTICES.md`.

[Centro de documentación](docs/README.md) · [Guía histórica en español](docs/i18n/README.es.md) · [Seguridad de pagos](docs/SAFETY.md)
