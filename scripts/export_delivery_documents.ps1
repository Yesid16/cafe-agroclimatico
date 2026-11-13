param([switch]$OnlyReport)

# Exportación local con Microsoft Word. No modifica los archivos DOCX.
$ErrorActionPreference = 'Stop'
$deliveryProject = Split-Path -Parent $PSScriptRoot
$deliveryRoot = Join-Path $deliveryProject 'Docs_Entregables'
$deliveryNames = if ($OnlyReport) { @('INFORME') } else {
    @('INFORME', 'evaluacion_agente', 'declaracion_uso_IA')
}
$deliveryWord = New-Object -ComObject Word.Application
$deliveryWord.Visible = $false
$deliveryWord.DisplayAlerts = 0
try {
    foreach ($deliveryName in $deliveryNames) {
        $deliveryDoc = $deliveryWord.Documents.Open((Join-Path $deliveryRoot ($deliveryName + '.docx')), $false, $true)
        try {
            $deliveryDoc.ExportAsFixedFormat((Join-Path $deliveryRoot ($deliveryName + '.pdf')), 17)
            Write-Output ('PDF: ' + $deliveryName)
        } finally { $deliveryDoc.Close(0) }
    }
} finally {
    $deliveryWord.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($deliveryWord)
}
$deliveryOutput = Join-Path $deliveryProject 'output/pdf'
New-Item -ItemType Directory -Force -Path $deliveryOutput | Out-Null
Copy-Item -LiteralPath (Join-Path $deliveryRoot 'INFORME.pdf') -Destination (Join-Path $deliveryOutput 'INFORME.pdf')
