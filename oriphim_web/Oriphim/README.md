# Oriphim Web Dashboard

## Project Overview

**Production URL**: https://oriphim.com

Oriphim is an AI-driven options trading automation platform that enables users to deploy sophisticated trading bots with professional risk management and real-time monitoring capabilities.

## Features

- **Automated Options Trading**: Deploy proven strategies like cash-secured puts, covered calls, and iron condors
- **Real-time Dashboard**: Monitor positions, P/L, and bot performance with live market data
- **Desktop Integration**: Seamless connection with the Oriphim Runner desktop application
- **Professional Risk Management**: Built-in position sizing, stop-losses, and drawdown controls
- **Interactive Broker Integration**: Direct connection to IBKR for live trading and paper trading
- **Real-time Notifications**: Instant alerts for trades, errors, and system status

## Development Setup

### Prerequisites

- Node.js 18+ and npm - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- Git for version control

### Local Development

```sh
# Clone the repository
git clone https://github.com/v5ph/oriphim-web.git

# Navigate to the web application directory
cd oriphim-web/oriphim_web/Oriphim

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Add your Supabase credentials to .env
# REACT_APP_SUPABASE_URL=your-supabase-url
# REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key

# Start the development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Build for Production

```sh
# Create production build
npm run build

# Preview production build locally
npm run preview
```

## Technology Stack

### Frontend
- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development with full IntelliSense
- **Vite** - Fast build tool with hot module replacement
- **Tailwind CSS** - Utility-first CSS framework for rapid styling
- **shadcn/ui** - High-quality, accessible React components
- **Lucide React** - Beautiful, customizable SVG icons

### Backend & Infrastructure
- **Supabase** - PostgreSQL database with real-time subscriptions
- **Supabase Edge Functions** - Serverless functions for backend logic
- **Row Level Security** - Database-level security and authorization
- **Real-time Subscriptions** - Live updates for trades and bot status

### Integrations
- **Interactive Brokers API** - Live trading and market data via IBKR
- **Desktop Runner Integration** - Seamless connection with Python trading engine
- **Real-time Charts** - Live market data visualization
- **WebSocket Connections** - Real-time communication with trading systems

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui base components
│   ├── dashboard/      # Dashboard-specific components
│   └── charts/         # Trading chart components
├── pages/              # Page components and routing
│   ├── dashboard/      # Dashboard pages (Overview, Bots, etc.)
│   └── auth/           # Authentication pages
├── hooks/              # Custom React hooks
├── lib/                # Utility functions and configurations
├── contexts/           # React context providers
└── assets/             # Static assets and images
```

## Environment Configuration

Required environment variables:

```env
# Supabase Configuration
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key

# Optional: Analytics and Monitoring
REACT_APP_ANALYTICS_ID=your-analytics-id
```

## Deployment

### Production Deployment
The application is deployed at **https://oriphim.com** using modern web hosting with:
- SSL/TLS encryption
- CDN distribution
- Automatic builds from the main branch
- Environment variable management

### Development Deployment
For staging and testing:
```sh
npm run build
npm run preview
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For technical support and questions:
- **Documentation**: Visit the project wiki
- **Issues**: Report bugs via GitHub issues
- **Email**: support@oriphim.com

## License

This project is proprietary software. All rights reserved.
