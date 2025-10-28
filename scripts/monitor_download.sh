#!/bin/bash
# Monitor Kraken2 database download progress

DB_FILE="$HOME/kraken2_db/k2_pluspfp_16gb_20240112.tar.gz"
EXPECTED_SIZE=11222290598  # 10.5GB in bytes

while true; do
    if [ -f "$DB_FILE" ]; then
        CURRENT_SIZE=$(stat -c%s "$DB_FILE")
        PERCENT=$((CURRENT_SIZE * 100 / EXPECTED_SIZE))
        CURRENT_GB=$(echo "scale=2; $CURRENT_SIZE / 1073741824" | bc)
        EXPECTED_GB=$(echo "scale=2; $EXPECTED_SIZE / 1073741824" | bc)
        
        echo -ne "\rDownload Progress: ${CURRENT_GB}GB / ${EXPECTED_GB}GB (${PERCENT}%)"
        
        if [ "$CURRENT_SIZE" -ge "$EXPECTED_SIZE" ]; then
            echo -e "\n✅ Download complete!"
            break
        fi
    else
        echo "File not found: $DB_FILE"
        break
    fi
    
    sleep 5
done

echo ""
echo "Next steps:"
echo "1. Extract the database: tar -xzf $DB_FILE -C ~/kraken2_db/"
echo "2. Run tests: bash scripts/test_kraken2_pipeline.sh"