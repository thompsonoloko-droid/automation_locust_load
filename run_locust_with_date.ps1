# Usage: Run Locust and append output with date to reports/locust_run_results.txt
# Example PowerShell command:

# $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
# "==== Locust Run: $date ====" | Out-File -FilePath reports/locust_run_results.txt -Append -Encoding utf8
# locust -f tests/locustfile.py *>&1 | ForEach-Object { $_ -replace "\0", "" } | Out-File -FilePath reports/locust_run_results.txt -Append -Encoding utf8

# Or as a batch script (run_locust_with_date.bat):
# @echo off
# set DATESTR=%date% %time%
# echo ==== Locust Run: %DATESTR% ====>> reports\locust_run_results.txt
# locust -f tests/locustfile.py >> reports\locust_run_results.txt
