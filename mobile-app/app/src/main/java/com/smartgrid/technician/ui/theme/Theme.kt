package com.smartgrid.technician.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val AppColorScheme = lightColorScheme(
    primary = ElectricBlue,
    onPrimary = OnElectricBlue,
    primaryContainer = ElectricBlueContainer,
    onPrimaryContainer = OnElectricBlueContainer,
    secondary = SlateBlue,
    onSecondary = OnElectricBlue,
    secondaryContainer = SlateContainer,
    onSecondaryContainer = OnSlate,
    tertiary = ElectricBlueLight,
    onTertiary = OnElectricBlue,
    background = AppBackground,
    onBackground = AppTextPrimary,
    surface = AppSurface,
    onSurface = AppTextPrimary,
    surfaceVariant = AppSurfaceVariant,
    onSurfaceVariant = SlateBlue,
    outline = AppOutline,
    error = ErrorRed,
    onError = OnElectricBlue,
    errorContainer = ErrorRedContainer,
    onErrorContainer = ErrorRed
)

@Composable
fun SmartGridTheme(
    darkTheme: Boolean = false,
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = AppColorScheme,
        typography = Typography,
        content = content
    )
}
