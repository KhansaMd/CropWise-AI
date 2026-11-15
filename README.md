🌱 CropWise AI

Climate-Informed Agricultural Decision Support

Smarter Crop Rotations. Stronger Farms. A More Resilient India.

CropWise AI is a web-based agricultural decision-support platform that transforms NASA satellite-derived and meteorological climate datasets into accessible agricultural insights.

By combining historical and recent observations from NASA POWER with transparent crop rotation comparisons, CropWise AI helps farmers explore local climate conditions and understand factors that may influence agricultural planning.

Developed as part of the 2026 NASA Space Apps Challenge, the project demonstrates how openly accessible Earth science data can support more informed and climate-aware decision-making.

Important: CropWise AI is a research prototype. Its crop rotation comparisons and provisional scores are illustrative team estimates, not scientifically validated crop suitability recommendations.

🌍 The Problem

Agriculture is increasingly affected by climate variability.

Farmers face challenges including:

Unpredictable rainfall patterns and seasonal precipitation changes.

Rising temperatures and prolonged heat exposure.

Extended dry spells affecting water availability.

Uncertainty when selecting crops and planning rotations.

Limited access to understandable, location-specific climate information.

Although valuable environmental data is publicly available through NASA, translating these datasets into practical agricultural insights remains challenging.

CropWise AI bridges this gap by making climate observations easier to explore, interpret, and compare with example cropping strategies.

💡 Our Solution

CropWise AI provides a simple, interactive experience that connects climate information with agricultural decision support.

Users can:

Select a district from the supported pilot locations.

Enter a farm profile, including current crop, water availability, soil type, and farming priorities.

Explore seasonal climate insights derived from NASA POWER observations.

Compare example crop rotations using transparent, provisional scoring indicators.

Review supporting evidence, missing information, and limitations before considering agricultural decisions.

The platform emphasizes explainability and responsible interpretation rather than presenting unverified recommendations as facts.

✨ Key Features

🌦️ Seasonal Climate Dashboard

Explore district-level climate indicators, including:

Seasonal rainfall variation relative to historical baselines.

Temperature anomalies.

Longest consecutive dry spells.

Heat-day indicators.

Seasonal data quality and observation completeness.

The dashboard presents environmental observations in a farmer-friendly format.

🌾 Crop Rotation Explorer

Compare three example crop rotation sequences for a selected district.

Each comparison may include:

Crop sequence and rotation description.

Provisional overall comparison score.

Available water and climate-resilience indicators.

Confidence levels.

Supporting crop evidence.

Missing assessment criteria.

Expert-review requirements.

Detailed explanations of the comparison.

Scores are illustrative team estimates and should not be interpreted as validated agronomic suitability rankings.

📍 District-Level Exploration

CropWise AI currently supports four pilot districts across India:

State

District

Punjab

Ludhiana

Bihar

Samastipur

Maharashtra

Akola

Tamil Nadu

Thanjavur

These locations provide a foundation for exploring climate variability across different agricultural regions.

🔍 Transparent Decision Support

CropWise AI explicitly communicates:

Which indicators are based on NASA climate observations.

Which crop-related values are illustrative estimates.

Which criteria lack sufficient information.

Where agricultural expert validation is required.

This transparency is central to the project's approach.

🛰️ NASA Data Integration

CropWise AI uses the NASA POWER (Prediction Of Worldwide Energy Resources) Daily API.

Data source: NASA POWER Daily API

API endpoint:

https://power.larc.nasa.gov/api/temporal/daily/point

Environmental Parameters

Parameter

Description

Application

T2M

Daily average air temperature at 2 metres

Seasonal temperature analysis

T2M_MAX

Daily maximum air temperature at 2 metres

Heat-related indicators

PRECTOTCORR

Corrected precipitation

Rainfall variation and dry-spell analysis

ALLSKY_SFC_SW_DWN

All-sky surface shortwave downward radiation

Environmental context

How NASA Data Is Used

NASA POWER observations are retrieved and processed by the CropWise AI backend.

The processing pipeline transforms daily environmental observations into seasonal summaries that can be explored through the web interface.

These summaries help users understand local rainfall and temperature patterns when examining example crop rotations.

NASA provides the environmental observations. CropWise AI performs the data processing, interpretation, comparison, and visualization.

NASA does not directly provide the crop rotation recommendations or provisional scores displayed by this application.

🏗️ System Architecture

             NASA POWER Daily API
                      |
                      v
            Python Data Processing
                      |
                      v
          Climate Indicators & Data
                      |
                      v
             Backend REST APIs
               /           \
              v             v
      Climate Summary   Rotation Comparison
              \             /
               v           v
             React Frontend
                      |
                      v
          CropWise AI Web Interface

Application Workflow

1. Data acquisition

Retrieve historical and recent climate observations for supported district locations using NASA POWER.

2. Climate processing

Process daily observations into seasonal indicators, including rainfall variation, temperature anomalies, and dry spells.

3. Rotation comparison

Use crop profiles, example rotation sequences, and available climate indicators to generate provisional comparisons.

4. API communication

Expose processed climate information and rotation comparison results through backend endpoints.

5. Frontend visualization

Present climate indicators, crop sequences, evidence, missing criteria, and confidence warnings in an accessible interface.

💻 Technology Stack

Layer

Technology

Frontend

React, JavaScript, Vite

Styling

CSS, Tailwind CSS utility classes

Icons

Lucide React

Backend

Python

API framework

FastAPI

Climate data

NASA POWER Daily API

Data processing

Python-based climate processing modules

Data storage

Local JSON and Parquet data files

Version control

Git and GitHub

Deployment

Frontend and backend hosting to be confirmed

The current prototype uses file-based climate datasets and application data. A production database service has not been established as a project requirement.

🔌 API Integration

The frontend communicates with backend services for climate summaries and crop rotation comparisons.

Crop Rotation Comparison

POST /api/rotation/compare

This endpoint processes the relevant inputs and returns rotation comparison information, including available scores, confidence indicators, evidence, and limitations.

The climate summary API provides district-level seasonal climate information for the dashboard.

For full request schemas, available endpoints, and response formats, refer to the backend's automatically generated FastAPI documentation at /docs when the backend is running.

🚀 Getting Started

Prerequisites

Node.js and npm

Python

Git

1. Clone the Repository

git clone https://github.com/KhansaMd/CropWise-AI.git
cd CropWise-AI

2. Set Up the Frontend

cd frontend
npm install
npm run dev

Open the local URL displayed by Vite, typically:

http://localhost:5173

3. Set Up the Backend

Open another terminal from the repository root:

cd backend
python -m venv .venv

Activate the environment.

Windows:

.venv\Scripts\Activate.ps1

macOS/Linux:

source .venv/bin/activate

Install the dependencies:

pip install -r requirements.txt

Start the API using the command specified in backend/README.md.

The exact backend startup command and frontend API environment configuration should be verified against the final integrated branch.

4. Run Backend Tests

From the backend directory:

python -m pytest

The backend integration team reported 30 passing tests during development. Test results should be reconfirmed against the final merged version.

📊 Data Reliability and Limitations

CropWise AI is designed to distinguish between observed environmental data and provisional agricultural comparisons.

NASA Climate Observations

Climate indicators are calculated from NASA POWER environmental observations.

They describe historical or recent environmental conditions and are not forecasts of future weather, crop yield, or farm profitability.

Illustrative Rotation Scores

Some comparison components use team-estimated values.

These estimates are not independently validated crop suitability assessments.

Where sufficient information is unavailable, the platform identifies missing criteria rather than inventing verified results.

Agricultural Validation

Crop rotation decisions depend on additional factors, including:

Local soil conditions and soil testing.

Irrigation infrastructure.

Crop-specific growing requirements.

Pest and disease risks.

Local cropping calendars.

Input costs and market conditions.

Expert agronomic assessment.

Users should consult local agricultural universities, ICAR, Krishi Vigyan Kendras (KVKs), or qualified agricultural experts before making farming decisions.

🌱 Expected Impact

CropWise AI aims to:

Improve climate-data accessibility

Make NASA environmental observations easier to explore for agricultural users.

Support climate awareness

Help users understand seasonal climate variability in their districts.

Encourage informed crop planning

Provide a structured way to compare possible cropping sequences while communicating uncertainties.

Promote transparent agricultural technology

Demonstrate how decision-support systems can communicate evidence, limitations, and confidence instead of producing unexplained recommendations.

Create a foundation for future research

Support future collaboration with agricultural experts and local institutions.

🔮 Future Development

Potential next steps include:

Expanding coverage to additional agricultural districts.

Incorporating validated crop-specific agronomic datasets.

Integrating verified soil and irrigation information.

Improving seasonal visualization and historical comparisons.

Developing multilingual accessibility.

Adding expert-reviewed crop suitability models.

Evaluating recommendations through agricultural field studies.

Improving infrastructure for scalable deployment.

These are proposed improvements, not features claimed to be complete in the current prototype.

👥 Team and Collaboration

CropWise AI was developed collaboratively for the 2026 NASA Space Apps Challenge.

The project combines frontend development, climate data processing, backend API development, crop rotation comparison logic, research, and project documentation.

Team member names and individual contributions can be added here before the final submission.

📚 References and Resources

NASA POWER Project: https://power.larc.nasa.gov/

NASA POWER Daily API: https://power.larc.nasa.gov/api/temporal/daily/point

NASA Space Apps Challenge: https://www.spaceappschallenge.org/

Indian Council of Agricultural Research: https://icar.gov.in/

⚠️ Disclaimer

CropWise AI is an educational and research-oriented prototype developed for a hackathon.

Its climate indicators are derived from environmental observations, while its crop rotation comparisons contain provisional and illustrative team estimates.

The application does not provide validated agricultural prescriptions, guaranteed yield predictions, or professional farming advice.

Agricultural decisions should be made with appropriate local data and qualified expert guidance.

🌍 CropWise AI

Turning Earth observations into clearer agricultural insights.

Smarter Crop Rotations. Stronger Farms. A More Resilient India.
