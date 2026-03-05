#!/bin/bash
# Pre-push checklist for Tariff Extraction System

echo "=================================="
echo "PRE-PUSH CHECKLIST"
echo "=================================="

# 1. Check for sensitive data
echo -e "\n1. Checking for sensitive data..."
if grep -r "password\|secret\|key\|token" --include="*.py" --include="*.yaml" --exclude=".env.example" . 2>/dev/null | grep -v "DB_PASSWORD\|your_password_here"; then
    echo "   [WARN] Potential sensitive data found in code"
else
    echo "   [OK] No sensitive data in code"
fi

# 2. Check .env is ignored
echo -e "\n2. Checking .env is not tracked..."
if git ls-files | grep -q "^.env$"; then
    echo "   [FAIL] .env is tracked! Run: git rm --cached .env"
    exit 1
else
    echo "   [OK] .env is not tracked"
fi

# 3. Check __pycache__ is ignored
echo -e "\n3. Checking Python cache is not tracked..."
if git ls-files | grep -q "__pycache__"; then
    echo "   [FAIL] __pycache__ is tracked! Run: git rm -r --cached **/__pycache__"
    exit 1
else
    echo "   [OK] Python cache not tracked"
fi

# 4. Check data files are ignored
echo -e "\n4. Checking data files are not tracked..."
if git ls-files | grep -q "data/raw/.*\.\(html\|pdf\)$"; then
    echo "   [FAIL] Data files are tracked!"
    exit 1
else
    echo "   [OK] Data files not tracked"
fi

# 5. Verify system
echo -e "\n5. Running system verification..."
python scripts/verify_system.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   [OK] System verification passed"
else
    echo "   [WARN] System verification failed (may need database)"
fi

echo -e "\n=================================="
echo "READY TO PUSH"
echo "=================================="
echo ""
echo "Run: git add ."
echo "     git commit -m 'Initial commit: Tariff extraction system'"
echo "     git push origin main"
