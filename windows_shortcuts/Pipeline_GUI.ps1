# Equine Microbiome Reporter - Windows GUI
# PowerShell script with Windows Forms interface

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Equine Microbiome Reporter - HippoVet+"
$form.Size = New-Object System.Drawing.Size(600,500)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false

# Add icon/logo area
$pictureBox = New-Object System.Windows.Forms.PictureBox
$pictureBox.Size = New-Object System.Drawing.Size(560,80)
$pictureBox.Location = New-Object System.Drawing.Point(20,10)
$pictureBox.BackColor = [System.Drawing.Color]::FromArgb(30,58,138)
$form.Controls.Add($pictureBox)

# Title label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "EQUINE MICROBIOME REPORTER"
$titleLabel.Font = New-Object System.Drawing.Font("Arial",16,[System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::White
$titleLabel.BackColor = [System.Drawing.Color]::FromArgb(30,58,138)
$titleLabel.Size = New-Object System.Drawing.Size(540,30)
$titleLabel.Location = New-Object System.Drawing.Point(30,30)
$titleLabel.TextAlign = "MiddleCenter"
$form.Controls.Add($titleLabel)

# Subtitle
$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Text = "Automated 16S rRNA Analysis Pipeline"
$subtitleLabel.Font = New-Object System.Drawing.Font("Arial",10)
$subtitleLabel.ForeColor = [System.Drawing.Color]::White
$subtitleLabel.BackColor = [System.Drawing.Color]::FromArgb(30,58,138)
$subtitleLabel.Size = New-Object System.Drawing.Size(540,20)
$subtitleLabel.Location = New-Object System.Drawing.Point(30,55)
$subtitleLabel.TextAlign = "MiddleCenter"
$form.Controls.Add($subtitleLabel)

# Input directory section
$inputLabel = New-Object System.Windows.Forms.Label
$inputLabel.Text = "FASTQ Input Directory:"
$inputLabel.Location = New-Object System.Drawing.Point(20,110)
$inputLabel.Size = New-Object System.Drawing.Size(150,20)
$form.Controls.Add($inputLabel)

$inputTextBox = New-Object System.Windows.Forms.TextBox
$inputTextBox.Location = New-Object System.Drawing.Point(20,130)
$inputTextBox.Size = New-Object System.Drawing.Size(450,20)
$inputTextBox.Text = "C:\Users\$env:USERNAME\Desktop\fastq_files"
$form.Controls.Add($inputTextBox)

$inputBrowseButton = New-Object System.Windows.Forms.Button
$inputBrowseButton.Location = New-Object System.Drawing.Point(480,128)
$inputBrowseButton.Size = New-Object System.Drawing.Size(80,24)
$inputBrowseButton.Text = "Browse..."
$inputBrowseButton.Add_Click({
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = "Select FASTQ input directory"
    if ($folderBrowser.ShowDialog() -eq "OK") {
        $inputTextBox.Text = $folderBrowser.SelectedPath
    }
})
$form.Controls.Add($inputBrowseButton)

# Output directory section
$outputLabel = New-Object System.Windows.Forms.Label
$outputLabel.Text = "Output Directory:"
$outputLabel.Location = New-Object System.Drawing.Point(20,170)
$outputLabel.Size = New-Object System.Drawing.Size(150,20)
$form.Controls.Add($outputLabel)

$outputTextBox = New-Object System.Windows.Forms.TextBox
$outputTextBox.Location = New-Object System.Drawing.Point(20,190)
$outputTextBox.Size = New-Object System.Drawing.Size(450,20)
$dateStr = Get-Date -Format "yyyyMMdd"
$outputTextBox.Text = "C:\Users\$env:USERNAME\Desktop\results_$dateStr"
$form.Controls.Add($outputTextBox)

$outputBrowseButton = New-Object System.Windows.Forms.Button
$outputBrowseButton.Location = New-Object System.Drawing.Point(480,188)
$outputBrowseButton.Size = New-Object System.Drawing.Size(80,24)
$outputBrowseButton.Text = "Browse..."
$outputBrowseButton.Add_Click({
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = "Select output directory"
    if ($folderBrowser.ShowDialog() -eq "OK") {
        $outputTextBox.Text = $folderBrowser.SelectedPath
    }
})
$form.Controls.Add($outputBrowseButton)

# Options section
$optionsGroup = New-Object System.Windows.Forms.GroupBox
$optionsGroup.Text = "Processing Options"
$optionsGroup.Location = New-Object System.Drawing.Point(20,230)
$optionsGroup.Size = New-Object System.Drawing.Size(560,80)
$form.Controls.Add($optionsGroup)

$parallelCheckBox = New-Object System.Windows.Forms.CheckBox
$parallelCheckBox.Text = "Enable parallel processing (faster)"
$parallelCheckBox.Location = New-Object System.Drawing.Point(10,25)
$parallelCheckBox.Size = New-Object System.Drawing.Size(250,20)
$parallelCheckBox.Checked = $true
$optionsGroup.Controls.Add($parallelCheckBox)

$excelCheckBox = New-Object System.Windows.Forms.CheckBox
$excelCheckBox.Text = "Generate Excel review files"
$excelCheckBox.Location = New-Object System.Drawing.Point(10,50)
$excelCheckBox.Size = New-Object System.Drawing.Size(250,20)
$excelCheckBox.Checked = $true
$optionsGroup.Controls.Add($excelCheckBox)

$pdfCheckBox = New-Object System.Windows.Forms.CheckBox
$pdfCheckBox.Text = "Generate PDF reports"
$pdfCheckBox.Location = New-Object System.Drawing.Point(280,25)
$pdfCheckBox.Size = New-Object System.Drawing.Size(250,20)
$pdfCheckBox.Checked = $true
$optionsGroup.Controls.Add($pdfCheckBox)

$openCheckBox = New-Object System.Windows.Forms.CheckBox
$openCheckBox.Text = "Open results when complete"
$openCheckBox.Location = New-Object System.Drawing.Point(280,50)
$openCheckBox.Size = New-Object System.Drawing.Size(250,20)
$openCheckBox.Checked = $true
$optionsGroup.Controls.Add($openCheckBox)

# Progress text box
$progressTextBox = New-Object System.Windows.Forms.TextBox
$progressTextBox.Multiline = $true
$progressTextBox.ScrollBars = "Vertical"
$progressTextBox.Location = New-Object System.Drawing.Point(20,320)
$progressTextBox.Size = New-Object System.Drawing.Size(560,80)
$progressTextBox.ReadOnly = $true
$progressTextBox.BackColor = [System.Drawing.Color]::Black
$progressTextBox.ForeColor = [System.Drawing.Color]::LightGreen
$progressTextBox.Font = New-Object System.Drawing.Font("Consolas",9)
$form.Controls.Add($progressTextBox)

# Buttons
$processButton = New-Object System.Windows.Forms.Button
$processButton.Location = New-Object System.Drawing.Point(20,420)
$processButton.Size = New-Object System.Drawing.Size(150,35)
$processButton.Text = "START PROCESSING"
$processButton.BackColor = [System.Drawing.Color]::FromArgb(16,185,129)
$processButton.ForeColor = [System.Drawing.Color]::White
$processButton.Font = New-Object System.Drawing.Font("Arial",10,[System.Drawing.FontStyle]::Bold)
$processButton.FlatStyle = "Flat"
$processButton.Add_Click({
    $progressTextBox.Clear()
    $progressTextBox.AppendText("Starting pipeline...`r`n")
    
    # Convert paths for WSL
    $inputPath = $inputTextBox.Text
    $outputPath = $outputTextBox.Text
    
    # Convert to WSL paths
    $wslInput = "/mnt/" + $inputPath[0].ToString().ToLower() + "/" + $inputPath.Substring(3).Replace('\','/')
    $wslOutput = "/mnt/" + $outputPath[0].ToString().ToLower() + "/" + $outputPath.Substring(3).Replace('\','/')
    
    $progressTextBox.AppendText("Input: $inputPath`r`n")
    $progressTextBox.AppendText("Output: $outputPath`r`n")
    $progressTextBox.AppendText("Processing...`r`n")
    
    # Build command
    $command = "cd ~/equine-microbiome-reporter && conda activate equine-microbiome && python scripts/full_pipeline.py --input-dir '$wslInput' --output-dir '$wslOutput'"
    
    # Run in WSL2
    $process = Start-Process -FilePath "wsl" -ArgumentList "-d Ubuntu -e bash -c `"$command`"" -PassThru -NoNewWindow -Wait
    
    if ($process.ExitCode -eq 0) {
        $progressTextBox.AppendText("`r`nSUCCESS! Processing complete.`r`n")
        
        if ($openCheckBox.Checked) {
            Start-Process "explorer.exe" -ArgumentList $outputPath
        }
    } else {
        $progressTextBox.AppendText("`r`nERROR: Pipeline failed. Check logs for details.`r`n")
    }
})
$form.Controls.Add($processButton)

$demoButton = New-Object System.Windows.Forms.Button
$demoButton.Location = New-Object System.Drawing.Point(180,420)
$demoButton.Size = New-Object System.Drawing.Size(120,35)
$demoButton.Text = "Run Demo"
$demoButton.BackColor = [System.Drawing.Color]::FromArgb(59,130,246)
$demoButton.ForeColor = [System.Drawing.Color]::White
$demoButton.Font = New-Object System.Drawing.Font("Arial",10)
$demoButton.FlatStyle = "Flat"
$demoButton.Add_Click({
    $progressTextBox.Clear()
    $progressTextBox.AppendText("Running demo with test data...`r`n")
    
    Start-Process -FilePath "wsl" -ArgumentList "-d Ubuntu -e bash -c `"cd ~/equine-microbiome-reporter && conda activate equine-microbiome && ./demo.sh`"" -Wait
    
    $progressTextBox.AppendText("Demo complete!`r`n")
})
$form.Controls.Add($demoButton)

$updateButton = New-Object System.Windows.Forms.Button
$updateButton.Location = New-Object System.Drawing.Point(310,420)
$updateButton.Size = New-Object System.Drawing.Size(120,35)
$updateButton.Text = "Check Updates"
$updateButton.BackColor = [System.Drawing.Color]::FromArgb(251,146,60)
$updateButton.ForeColor = [System.Drawing.Color]::White
$updateButton.Font = New-Object System.Drawing.Font("Arial",10)
$updateButton.FlatStyle = "Flat"
$updateButton.Add_Click({
    $progressTextBox.Clear()
    $progressTextBox.AppendText("Checking for updates...`r`n")
    
    Start-Process -FilePath "wsl" -ArgumentList "-d Ubuntu -e bash -c `"cd ~/equine-microbiome-reporter && git pull origin main`"" -Wait
    
    $progressTextBox.AppendText("Update check complete!`r`n")
})
$form.Controls.Add($updateButton)

$exitButton = New-Object System.Windows.Forms.Button
$exitButton.Location = New-Object System.Drawing.Point(480,420)
$exitButton.Size = New-Object System.Drawing.Size(100,35)
$exitButton.Text = "Exit"
$exitButton.BackColor = [System.Drawing.Color]::Gray
$exitButton.ForeColor = [System.Drawing.Color]::White
$exitButton.Font = New-Object System.Drawing.Font("Arial",10)
$exitButton.FlatStyle = "Flat"
$exitButton.Add_Click({ $form.Close() })
$form.Controls.Add($exitButton)

# Show the form
$form.ShowDialog()