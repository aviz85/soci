#!/bin/bash

# Set environment variable for Django settings
export DJANGO_SETTINGS_MODULE=socisphere.settings

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies if requirements-test.txt exists
if [ -f "tests/requirements-test.txt" ]; then
    pip install -r tests/requirements-test.txt
fi

# Install pytest-cov if not already installed
pip install pytest-cov

# Run notification tests with coverage
pytest tests/interactions/test_notification_*.py tests/client/test_notification_*.py \
    --cov=apps.interactions.models \
    --cov=apps.interactions.views \
    --cov=apps.interactions.serializers \
    --cov=static/js/notifications.js \
    --cov-report=term-missing \
    --cov-report=html:coverage_reports/notification_coverage

# Provide feedback on test results
echo "-----------------------------------------------------"
echo "Notification tests complete. Coverage report saved to:"
echo "coverage_reports/notification_coverage/index.html"
echo "-----------------------------------------------------"

# Create the coverage badge if possible
if [ -f "venv/bin/coverage-badge" ]; then
    venv/bin/coverage-badge -o coverage_reports/notification_coverage_badge.svg
    echo "Coverage badge generated at coverage_reports/notification_coverage_badge.svg"
fi

# Return to original directory if needed
echo "Tests complete." 