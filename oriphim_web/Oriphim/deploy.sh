#!/bin/bash

# 🚀 Oriphim Cloudflare Deployment Script
# Automates the build and deployment process

set -e  # Exit on any error

echo "🚀 Starting Oriphim Cloudflare Deployment..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from oriphim_web/Oriphim directory"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Environment Check
print_status "Checking environment..."

# Check Node.js version
NODE_VERSION=$(node --version)
print_status "Node.js version: $NODE_VERSION"

if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_status "npm version: $NPM_VERSION"

# Step 2: Install dependencies
print_status "Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Step 3: Run linting
print_status "Running ESLint..."
npm run lint

if [ $? -eq 0 ]; then
    print_success "Linting passed"
else
    print_warning "Linting found issues, but continuing..."
fi

# Step 4: Build for production
print_status "Building for production..."
npm run build:production

if [ $? -eq 0 ]; then
    print_success "Build completed successfully"
else
    print_error "Build failed"
    exit 1
fi

# Step 5: Check build output
print_status "Checking build output..."

if [ ! -d "dist" ]; then
    print_error "dist directory not found"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    print_error "dist/index.html not found"
    exit 1
fi

# Check for essential files
ESSENTIAL_FILES=("dist/index.html" "dist/assets" "public/_redirects" "public/_headers")
for file in "${ESSENTIAL_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        print_warning "Missing file: $file"
    else
        print_success "Found: $file"
    fi
done

# Step 6: Analyze bundle size
print_status "Analyzing bundle size..."
BUILD_SIZE=$(du -sh dist | cut -f1)
print_status "Total build size: $BUILD_SIZE"

# Check for large files
find dist -name "*.js" -size +500k -exec echo "⚠️  Large JS file: {} ($(du -h {} | cut -f1))" \;
find dist -name "*.css" -size +100k -exec echo "⚠️  Large CSS file: {} ($(du -h {} | cut -f1))" \;

# Step 7: Security check
print_status "Running security checks..."

# Check for sensitive files in dist
SENSITIVE_PATTERNS=(".env" "config" "secret" "private" "key")
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if find dist -name "*$pattern*" | grep -q .; then
        print_error "Found sensitive files matching pattern: $pattern"
        find dist -name "*$pattern*"
        exit 1
    fi
done

print_success "Security check passed"

# Step 8: Test the build locally
print_status "Starting local preview server..."
echo "🌐 Testing build at http://localhost:4173"
echo "📝 Open another terminal and run: curl -I http://localhost:4173"
echo "⏹️  Press Ctrl+C to stop the server when testing is complete"

# Run preview in background and wait for user input
npm run preview &
PREVIEW_PID=$!

sleep 3

# Basic health check
if curl -s http://localhost:4173 > /dev/null; then
    print_success "Local preview server is running"
else
    print_warning "Could not reach local preview server"
fi

echo ""
echo "🔍 Manual Testing Checklist:"
echo "   ✅ Page loads without errors"
echo "   ✅ Navigation works"
echo "   ✅ Responsive design works"
echo "   ✅ No console errors"
echo ""
echo "Press Enter when testing is complete..."
read -p ""

# Kill preview server
kill $PREVIEW_PID 2>/dev/null

# Step 9: Generate deployment summary
print_status "Generating deployment summary..."

echo ""
echo "📊 DEPLOYMENT SUMMARY"
echo "========================"
echo "Build Size: $BUILD_SIZE"
echo "Node Version: $NODE_VERSION"
echo "Build Time: $(date)"
echo ""

# Check if environment variables are set for production
if [ -f ".env.production" ]; then
    print_success "Production environment file found"
else
    print_warning "No .env.production file found"
fi

echo "🎯 NEXT STEPS FOR CLOUDFLARE PAGES:"
echo "1. 📁 Upload dist/ folder to Cloudflare Pages"
echo "2. ⚙️  Configure build settings:"
echo "   - Framework preset: Vite"
echo "   - Build command: npm run build:production"
echo "   - Build output directory: dist"
echo "   - Node.js version: 18.x"
echo "3. 🌐 Configure custom domain (if needed)"
echo "4. ✅ Set environment variables in Pages settings"
echo ""

echo "📁 Files ready for deployment:"
find dist -type f | head -10
if [ $(find dist -type f | wc -l) -gt 10 ]; then
    echo "   ... and $(( $(find dist -type f | wc -l) - 10 )) more files"
fi

echo ""
print_success "🎉 Build completed successfully! Ready for Cloudflare Pages deployment."

echo ""
echo "🔗 Useful links:"
echo "   📖 Deployment Guide: ../CLOUDFLARE_DEPLOYMENT_GUIDE.md"
echo "   🌐 Cloudflare Pages: https://pages.cloudflare.com"
echo "   📊 Performance: Run 'npm run analyze' for bundle analysis"