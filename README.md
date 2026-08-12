# 🎓 Plataforma de Simulacros Virtuales VILLTECC - UNSA

![VILLTECC Banner](https://img.shields.io/badge/VILLTECC-Plataforma_Educativa-8b0000?style=for-the-badge&logo=google-scholar)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap_5-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

Bienvenido al repositorio oficial del **Sistema de Evaluación Académica Digital VILLTECC**, una plataforma web diseñada específicamente para gestionar, evaluar y diagnosticar el rendimiento de los postulantes a la **Universidad Nacional de San Agustín (UNSA)** de Arequipa.

---

## 🚀 Descripción del Proyecto

Este sistema resuelve el problema de la evaluación preuniversitaria tradicional mediante simulacros virtuales que replican la estructura oficial del examen de la UNSA (RCU N° 0220-2024). 

El gran diferencial de VILLTECC es su capacidad de generar **Reportes Diagnósticos en PDF** automatizados, permitiendo a padres y alumnos conocer no solo el puntaje final, sino las áreas de mejora específicas.

## ✨ Características Principales

* **🛡️ Registro Seguro y Controlado:** Los postulantes se registran usando su DNI como usuario único para evitar cuentas duplicadas y garantizar la veracidad de los datos.
* **📚 Exámenes Especializados:** Pruebas configuradas automáticamente según el área del postulante (Biomédicas, Ingenierías y Sociales) con su respectiva matriz de pesos.
* **📊 Reportes PDF Automáticos:** Generación instantánea de resultados detallados al finalizar el simulacro.
* **🎯 Cruce de Cachimbos (Match System):** Script integrado que lee el PDF oficial de resultados de la UNSA y lo cruza con la base de datos de usuarios para encontrar ingresantes automáticamente.
* **👨‍💻 Panel de Administración Avanzado:** Filtros personalizados para visualizar postulantes por carrera y gestionar pagos de reportes.

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3.10+ / Django
* **Frontend:** HTML5, CSS3, Bootstrap 5, Bootstrap Icons
* **Base de Datos:** SQLite3 (Desarrollo) / PostgreSQL (Producción recomendada)
* **Librerías Clave:** 
  * `PyPDF2` (Para lectura inteligente de resultados UNSA)
  * Frameworks de generación PDF

---

## ⚙️ Pasos para Levantar el Proyecto (Instalación local)

Sigue estos pasos para ejecutar el proyecto en tu propia computadora:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/tu-usuario/simulacro-unsa-villtecc.git](https://github.com/tu-usuario/simulacro-unsa-villtecc.git)
cd simulacro-unsa-villtecc
