# Lino AutoCare Copilot

Lino AutoCare Copilot is an independent, source-grounded RAG assistant for tyre, engine-oil, vehicle-maintenance and autocare-service questions.

It retrieves relevant information from approved local sources and sends that evidence to Amazon Nova 2 Lite through Amazon Bedrock. Generated answers must remain grounded in the retrieved sources and avoid inventing prices, stock availability or vehicle diagnoses.

## Architecture

```mermaid
flowchart LR
    A["User question"] --> B["Hybrid TF-IDF retriever"]
    B --> C["Approved Lino sources"]
    C --> D["Amazon Nova 2 Lite"]
    D --> E["Grounded answer and citations"]
```

## What works

- Searches approved maintenance and safety guidance
- Searches 178 historical tyre products across 88 normalized sizes
- Searches 43 historical engine-oil products
- Quotes confirmed vehicle-diagnostics pricing of ₦20,000
- Quotes confirmed wheel-alignment pricing of ₦3,000
- Labels historical product prices as unconfirmed
- Returns source metadata with every answer
- Detects urgent symptoms and adds safety warnings
- Retrieves Michelin tyre-damage guidance for tyre-bulge questions
- Refuses to invent unsupported service prices
- Rejects unrelated questions when retrieval support is insufficient
- Includes automated retrieval and safety tests

## Technology

- Python
- Amazon Bedrock
- Amazon Nova 2 Lite
- Boto3
- scikit-learn
- TF-IDF and cosine similarity
- Pytest
- Git and GitHub

## Project structure

```text
data/                         Approved knowledge and anonymized catalogues
scripts/                      Dataset preparation scripts
src/lino_autocare_copilot/    Retrieval, Bedrock and CLI code
tests/                        Automated tests
```

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in Git Bash on Windows:

```bash
source .venv/Scripts/activate
```

Install the project and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## AWS setup

Amazon Nova 2 Lite must be available through Amazon Bedrock in `us-east-1`.

The application uses the AWS credentials configured on the computer. Credentials are not stored in the source code or repository.

You can verify the configured AWS identity with:

```bash
aws sts get-caller-identity
```

## Usage

Ask about a confirmed service price:

```bash
python -m lino_autocare_copilot.cli "How much does wheel alignment cost?"
```

Ask a safety-related question:

```bash
python -m lino_autocare_copilot.cli "My tyre has a bulge. Can I continue driving?"
```

Ask about an unconfirmed price:

```bash
python -m lino_autocare_copilot.cli "How much does brake pad replacement cost?"
```

Each CLI request runs retrieval locally and then makes an Amazon Bedrock inference request.

## Tests

Run the local automated tests:

```bash
python -m pytest -q
```

The automated tests do not call Amazon Bedrock.

## Safety and data notes

Lino is not a substitute for physical vehicle inspection or professional diagnosis. Safety-critical symptoms should be assessed by a qualified technician.

The business records in this repository are anonymized historical data used for portfolio demonstration. Historical tyre and engine-oil prices must not be presented as confirmed current prices.

## Current limitations

- The application currently uses a command-line interface.
- Retrieval runs locally rather than through a managed vector database.
- The complete application has not yet been deployed as a serverless AWS API.
- Only explicitly confirmed current prices may be quoted.