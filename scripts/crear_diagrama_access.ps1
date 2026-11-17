# Crea un modelo relacional Access a partir de los metadatos de la base local.
# No importa filas y no modifica PostgreSQL, Neon ni Vercel.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$metadataPath = Join-Path $root '.access_schema.json'
$outputPath = Join-Path $root 'Diagrama_Relaciones_Practicas.accdb'

$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
if (Test-Path -LiteralPath $outputPath) {
  Remove-Item -LiteralPath $outputPath
}

$access = New-Object -ComObject Access.Application
$access.Visible = $false
try {
  $access.NewCurrentDatabase($outputPath, 12) # 12 = formato Access 2007-2016
  $db = $access.CurrentDb()

  # DAO DataTypeEnum values
  $dbText = 10; $dbLong = 4; $dbInteger = 3; $dbDouble = 7
  $dbDate = 8; $dbMemo = 12; $dbBoolean = 1; $dbBinary = 9
  $dbAutoIncrField = 16

  foreach ($tableName in ($metadata.columns | Select-Object -ExpandProperty table_name -Unique)) {
    $td = $db.CreateTableDef($tableName)
    $tableColumns = @($metadata.columns | Where-Object table_name -eq $tableName)
    foreach ($column in $tableColumns) {
      $pgType = [string]$column.data_type
      $fieldType = $dbText
      $fieldSize = 0
      switch -Regex ($pgType) {
        '^(smallint)$' { $fieldType = $dbInteger; break }
        '^(integer|bigint)$' { $fieldType = $dbLong; break }
        '^(numeric|decimal|real|double precision)$' { $fieldType = $dbDouble; break }
        '^(date|timestamp.*|time.*)$' { $fieldType = $dbDate; break }
        '^(boolean)$' { $fieldType = $dbBoolean; break }
        '^(bytea)$' { $fieldType = $dbBinary; break }
        '^(text|json|jsonb|USER-DEFINED|ARRAY)$' { $fieldType = $dbMemo; break }
        '^character varying$|^character$' {
          $size = [int]$column.character_maximum_length
          if ($size -gt 255 -or $size -le 0) { $fieldType = $dbMemo } else { $fieldType = $dbText; $fieldSize = $size }
          break
        }
        default { $fieldType = $dbMemo }
      }
      if ($column.is_pk -and $pgType -match '^(integer|bigint)$') {
        $fieldType = $dbLong
      }
      if ($fieldType -eq $dbText -and $fieldSize -eq 0) { $fieldSize = 255 }
      if ($fieldType -eq $dbText) { $field = $td.CreateField([string]$column.column_name, $fieldType, $fieldSize) }
      else { $field = $td.CreateField([string]$column.column_name, $fieldType) }
      if ($column.is_pk -and $pgType -match '^(integer|bigint)$') {
        $field.Attributes = $dbAutoIncrField
      }
      if ([string]$column.is_nullable -eq 'NO' -and -not $column.is_pk) {
        $field.Required = $true
      }
      $td.Fields.Append($field)
    }
    $db.TableDefs.Append($td)
    $pkColumns = @($tableColumns | Where-Object is_pk)
    if ($pkColumns.Count -gt 0) {
      $idx = $td.CreateIndex('PrimaryKey')
      $idx.Primary = $true
      $idx.Unique = $true
      foreach ($column in $pkColumns) {
        $idx.Fields.Append($idx.CreateField([string]$column.column_name))
      }
      $td.Indexes.Append($idx)
    }
  }

  foreach ($fk in $metadata.foreign_keys) {
    $relationName = [string]$fk.constraint_name
    if ($relationName.Length -gt 60) { $relationName = $relationName.Substring(0, 60) }
    $relation = $db.CreateRelation($relationName, [string]$fk.foreign_table, [string]$fk.table_name, 0)
    $relationField = $relation.CreateField([string]$fk.foreign_column)
    $relationField.ForeignName = [string]$fk.column_name
    $relation.Fields.Append($relationField)
    $db.Relations.Append($relation)
  }

  # Read-only orientation notes to make the model easier to explain in the defense.
  $guide = $db.CreateTableDef('Guia_lectura')
  $guide.Fields.Append($guide.CreateField('orden', $dbLong))
  $guide.Fields.Append($guide.CreateField('grupo', $dbText, 80))
  $guide.Fields.Append($guide.CreateField('descripcion', $dbText, 255))
  $db.TableDefs.Append($guide)
  $db.Execute("INSERT INTO Guia_lectura (orden, grupo, descripcion) VALUES (1, '1. Núcleo institucional', 'Programas y empresas son entidades principales; convenios relaciona empresa y programa.')")
  $db.Execute("INSERT INTO Guia_lectura (orden, grupo, descripcion) VALUES (2, '2. Personas y cargos', 'Personas se conecta con tutores_academicos y tutores_empresariales; una persona puede tener ambos cargos.')")
  $db.Execute("INSERT INTO Guia_lectura (orden, grupo, descripcion) VALUES (3, '3. Prácticas', 'Estudiantes, programas, empresas, convenios y ambos tutores se relacionan con practicas.')")
  $db.Execute("INSERT INTO Guia_lectura (orden, grupo, descripcion) VALUES (4, '4. Seguimiento', 'Seguimientos, evaluaciones y documentos dependen de una práctica; seguimientos también identifica tutor académico.')")
  $db.Execute("INSERT INTO Guia_lectura (orden, grupo, descripcion) VALUES (5, '5. Seguridad', 'usuarios_sistema pertenece a un rol; roles_modulos conecta roles con modulos y define permisos CRUD.')")
  $db.Close()
}
finally {
  $access.Quit()
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($access)
}
Write-Output "Archivo creado: $outputPath"

