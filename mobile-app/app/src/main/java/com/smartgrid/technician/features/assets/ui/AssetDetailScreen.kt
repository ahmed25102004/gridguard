package com.smartgrid.technician.features.assets.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Business
import androidx.compose.material.icons.filled.CalendarToday
import androidx.compose.material.icons.filled.CloudDone
import androidx.compose.material.icons.filled.ElectricBolt
import androidx.compose.material.icons.filled.ElectricalServices
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.DataSource
import com.smartgrid.technician.ui.theme.AppBackground
import com.smartgrid.technician.ui.theme.AppOutline
import com.smartgrid.technician.ui.theme.AppTextPrimary
import com.smartgrid.technician.ui.theme.ElectricBlue
import com.smartgrid.technician.ui.theme.ElectricBlueContainer
import com.smartgrid.technician.ui.theme.SlateBlue
import com.smartgrid.technician.ui.theme.SuccessGreen
import com.smartgrid.technician.ui.theme.SuccessGreenBorder
import com.smartgrid.technician.ui.theme.SuccessGreenContainer
import com.smartgrid.technician.ui.theme.WarningAmber
import com.smartgrid.technician.ui.theme.WarningAmberContainer
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AssetDetailScreen(
    assetId: String,
    viewModel: AssetDetailViewModel,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(assetId) {
        viewModel.loadAsset(assetId)
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = AppBackground,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Asset Specifications",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back to Asset List",
                            tint = Color.White
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadAsset(assetId, forceRefresh = true) }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh from Server",
                            tint = Color.White
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = ElectricBlue,
                    titleContentColor = Color.White
                )
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when {
                uiState.isLoading && uiState.asset == null -> {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(color = ElectricBlue)
                    }
                }
                uiState.errorMessage != null && uiState.asset == null -> {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.padding(24.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Warning,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.error,
                                modifier = Modifier.size(48.dp)
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "Asset Not Found",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.error
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = uiState.errorMessage ?: "Details unavailable.",
                                style = MaterialTheme.typography.bodySmall,
                                color = SlateBlue
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Button(
                                onClick = { viewModel.loadAsset(assetId, forceRefresh = true) },
                                colors = ButtonDefaults.buttonColors(containerColor = ElectricBlue),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Text("Retry")
                            }
                        }
                    }
                }
                uiState.asset != null -> {
                    AssetDetailContent(
                        asset = uiState.asset!!,
                        dataSource = uiState.dataSource,
                        isOffline = uiState.isOffline,
                        onRefresh = { viewModel.loadAsset(assetId, forceRefresh = true) }
                    )
                }
            }
        }
    }
}

@Composable
fun AssetDetailContent(
    asset: Asset,
    dataSource: DataSource,
    isOffline: Boolean,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // REQUIRED: Prominent Data-Source Banner ("Live Network" vs "Loaded from Cache")
        DataSourceBanner(
            dataSource = dataSource,
            isOffline = isOffline
        )

        // Asset Header Summary Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color.White
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(
                modifier = Modifier.padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CategoryBadge(category = asset.category)
                    OperationalStatusBadge(status = asset.status)
                }

                Text(
                    text = asset.name,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    color = AppTextPrimary
                )

                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.LocationOn,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = ElectricBlue
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "${asset.substationName ?: "General Substation"} (${asset.substationId ?: "N/A"})",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SlateBlue
                    )
                }
            }
        }

        // REQUIRED: Technical Specifications Card with all 6 core fields
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color.White
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(
                modifier = Modifier.padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Text(
                    text = "Required Technical Specifications",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = AppTextPrimary
                )

                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 2.dp),
                    color = AppOutline.copy(alpha = 0.5f)
                )

                // 1. Serial Number
                DetailSpecificationRow(
                    icon = Icons.Default.Fingerprint,
                    label = "Serial Number",
                    value = asset.serialNumber,
                    isMonospace = true,
                    highlight = true
                )

                // 2. Asset Category
                DetailSpecificationRow(
                    icon = Icons.Default.ElectricalServices,
                    label = "Asset Category",
                    value = asset.category.displayName
                )

                // 3. kVA Rating
                DetailSpecificationRow(
                    icon = Icons.Default.Speed,
                    label = "kVA Rating",
                    value = asset.formattedKvaRating
                )

                // 4. Voltage Class
                DetailSpecificationRow(
                    icon = Icons.Default.ElectricBolt,
                    label = "Voltage Class",
                    value = asset.formattedVoltageClass
                )

                // 5. Manufacturer
                DetailSpecificationRow(
                    icon = Icons.Default.Business,
                    label = "Manufacturer",
                    value = asset.formattedManufacturer
                )

                // 6. Installation Year
                DetailSpecificationRow(
                    icon = Icons.Default.CalendarToday,
                    label = "Installation Year",
                    value = asset.formattedInstallationYear
                )
            }
        }

        // Metadata & Security Integrity Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color.White
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(
                modifier = Modifier.padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = "Cache & Security Information",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = AppTextPrimary
                )

                DetailSpecificationRow(
                    icon = Icons.Default.Lock,
                    label = "Local Encryption",
                    value = "AES-256 (SQLCipher Keystore Vault)"
                )

                DetailSpecificationRow(
                    icon = Icons.Default.Storage,
                    label = "Local Cache Timestamp",
                    value = formatDateTime(asset.cachedAt)
                )

                if (asset.lastInspectedAt != null) {
                    DetailSpecificationRow(
                        icon = Icons.Default.Build,
                        label = "Last Field Inspection",
                        value = formatDateTime(asset.lastInspectedAt)
                    )
                }
            }
        }

        // Action Buttons
        OutlinedButton(
            onClick = onRefresh,
            modifier = Modifier
                .fillMaxWidth()
                .height(50.dp),
            shape = RoundedCornerShape(14.dp),
            border = BorderStroke(1.2.dp, ElectricBlue),
            colors = ButtonDefaults.outlinedButtonColors(
                containerColor = Color.White,
                contentColor = ElectricBlue
            )
        ) {
            Icon(
                imageVector = Icons.Default.Refresh,
                contentDescription = null,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "Re-Sync Live Specs from Server",
                fontWeight = FontWeight.SemiBold
            )
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

/**
 * Data Source Banner complying exactly with requirement:
 * - "Live Network when the displayed data was fetched from the backend"
 * - "Loaded from Cache when the displayed data came from local encrypted storage"
 */
@Composable
fun DataSourceBanner(
    dataSource: DataSource,
    isOffline: Boolean,
    modifier: Modifier = Modifier
) {
    val isLive = dataSource == DataSource.LIVE_NETWORK

    val backgroundColor = if (isLive) SuccessGreenContainer else WarningAmberContainer
    val borderColor = if (isLive) SuccessGreenBorder else WarningAmber.copy(alpha = 0.35f)
    val primaryTextColor = if (isLive) SuccessGreen else WarningAmber
    val bannerIcon: ImageVector = if (isLive) Icons.Default.CloudDone else Icons.Default.Storage

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        color = backgroundColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(primaryTextColor.copy(alpha = 0.14f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = bannerIcon,
                    contentDescription = null,
                    tint = primaryTextColor,
                    modifier = Modifier.size(22.dp)
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = dataSource.label,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = primaryTextColor
                    )

                    if (isOffline) {
                        Spacer(modifier = Modifier.width(8.dp))
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = MaterialTheme.colorScheme.errorContainer
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    imageVector = Icons.Default.WifiOff,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.onErrorContainer,
                                    modifier = Modifier.size(10.dp)
                                )
                                Spacer(modifier = Modifier.width(3.dp))
                                Text(
                                    text = "Offline",
                                    style = MaterialTheme.typography.labelSmall,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onErrorContainer
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(2.dp))

                Text(
                    text = if (isLive) {
                        "Synchronized directly from GridGuard Backend REST API"
                    } else {
                        "Retrieved securely from local AES-256 SQLCipher encrypted storage"
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = primaryTextColor.copy(alpha = 0.85f)
                )
            }
        }
    }
}

@Composable
fun DetailSpecificationRow(
    icon: ImageVector,
    label: String,
    value: String,
    isMonospace: Boolean = false,
    highlight: Boolean = false
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.weight(1f)
        ) {
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(CircleShape)
                    .background(ElectricBlueContainer),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = ElectricBlue,
                    modifier = Modifier.size(17.dp)
                )
            }
            Spacer(modifier = Modifier.width(10.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                color = SlateBlue
            )
        }

        Text(
            text = value,
            style = if (highlight) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodyMedium,
            fontWeight = if (highlight) FontWeight.Bold else FontWeight.SemiBold,
            fontFamily = if (isMonospace) FontFamily.Monospace else FontFamily.Default,
            color = if (highlight) ElectricBlue else AppTextPrimary
        )
    }
}

private fun formatDateTime(millis: Long): String {
    return try {
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        sdf.format(Date(millis))
    } catch (_: Exception) {
        "$millis"
    }
}
