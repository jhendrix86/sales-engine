# Sales Engine

Automated sales management system for the Autonomous Company OS. This engine handles lead management, CRM integration, pipeline tracking, closing automation, and sales analytics.

## Features

- **Lead Management** - Complete lead lifecycle management
- **CRM Integration** - HubSpot, Salesforce, Pipedrive integration
- **Pipeline Tracking** - Visual sales pipeline management
- **Automated Follow-ups** - Intelligent follow-up automation
- **Proposal Generation** - Automated proposal creation
- **Contract Management** - Contract lifecycle management
- **Sales Analytics** - Sales performance metrics and forecasting
- **Activity Tracking** - Complete sales activity logging

## Architecture

```
┌─────────────┐    Leads     ┌──────────────┐
│   All       │ ────────────> │  Lead        │
│  Sources    │               │  Ingestion   │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Lead       │ │ Pipeline│ │ Follow-up  │
            │   Manager    │ │ Engine  │ │  Engine    │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      CRM Integration            │
                    │  (HubSpot, Salesforce, etc.)    │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Proposal   │ │ Contract│ │ Analytics  │
            │   Generator  │ │ Manager │ │  Engine    │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for sales data)
- Redis (for caching and queues)
- CRM API keys (HubSpot, Salesforce, etc.)

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/sales-engine.git
cd sales-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8041
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f sales-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/sales` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `HUBSPOT_API_KEY` | - | HubSpot API key |
| `SALESFORCE_API_KEY` | - | Salesforce API key |
| `PIPEDRIVE_API_KEY` | - | Pipedrive API key |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Lead Management
- `POST /leads/create` - Create lead
- `POST /leads/{lead_id}/update` - Update lead
- `POST /leads/{lead_id}/convert` - Convert lead to opportunity
- `GET /leads/{lead_id}` - Get lead details
- `GET /leads` - List leads

### Pipeline Management
- `GET /pipeline/stages` - Get pipeline stages
- `POST /pipeline/move` - Move lead to pipeline stage
- `GET /pipeline/deals` - Get deals in pipeline
- `GET /pipeline/forecast` - Get pipeline forecast

### CRM Integration
- `POST /crm/sync` - Sync with CRM
- `GET /crm/status` - Get CRM sync status
- `POST /crm/webhook` - Handle CRM webhook

### Proposals
- `POST /proposals/generate` - Generate proposal
- `POST /proposals/{proposal_id}/send` - Send proposal
- `GET /proposals/{proposal_id}` - Get proposal details

### Analytics
- `GET /analytics/performance` - Get sales performance
- `GET /analytics/forecast` - Get sales forecast
- `GET /analytics/conversion` - Get conversion metrics

## Usage Examples

### Create Lead

```python
import httpx

async def create_lead():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8041/leads/create",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "company": "Acme Corp",
                "source": "marketing",
                "value": 10000
            }
        )
        return response.json()
```

### Move to Pipeline Stage

```python
async def move_pipeline_stage():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8041/pipeline/move",
            json={
                "lead_id": "lead_123",
                "stage": "proposal",
                "notes": "Ready for proposal"
            }
        )
        return response.json()
```

### Generate Proposal

```python
async def generate_proposal():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8041/proposals/generate",
            json={
                "lead_id": "lead_123",
                "template_id": "template_001",
                "customization": {}
            }
        )
        return response.json()
```

## Pipeline Stages

- **New** - Initial lead capture
- **Qualified** - Lead qualified by sales
- **Proposal** - Proposal sent
- **Negotiation** - Active negotiation
- **Closed Won** - Deal closed successfully
- **Closed Lost** - Deal lost

## CRM Integrations

- **HubSpot** - Full CRM integration
- **Salesforce** - Enterprise CRM integration
- **Pipedrive** - Sales-focused CRM integration
- **Custom** - Custom CRM API integration

## Integration with Other Engines

### Marketing Automation
- Receives qualified leads from marketing
- Updates lead scores based on sales activity
- Provides conversion data back to marketing

### Revenue Operations
- Creates opportunities in revenue system
- Updates revenue forecasts
- Handles contract billing

### Analytics Engine
- Provides sales performance data
- Tracks conversion metrics
- Generates sales forecasts

## Monitoring

### Metrics
- Lead conversion rate
- Pipeline velocity
- Average deal size
- Sales cycle length
- Win rate by stage
- Sales team performance

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
