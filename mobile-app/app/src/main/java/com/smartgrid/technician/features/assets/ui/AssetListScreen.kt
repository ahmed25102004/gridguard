package com.smartgrid.technician.features.assets.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Cable
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.ElectricalServices
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.AssetCategory
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AssetListScreen(
    viewModel: AssetListViewModel,
    onAssetClick: (Asset) -> Unit,
    onBackClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = AppBackground,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Grid Asset Registry",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Text(
                            text = if (uiState.isOffline) "Offline Local Cache" else "Live Cloud Sync Active",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.White.copy(alpha = 0.85f)
                        )
                    }
                },
                navigationIcon = {
                    if (onBackClick != null) {
                        IconButton(onClick = onBackClick) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Back to Workspace",
                                tint = Color.White
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadAssets(forceRefresh = true) }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh Assets",
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            Spacer(modifier = Modifier.height(6.dp))

            // Offline Availability Banner
            OfflineAvailabilityBanner(
                isOffline = uiState.isOffline,
                dataSource = uiState.dataSource,
                assetCount = uiState.assets.size
            )

            // Search Bar for Serial Number
            SearchBarSection(
                query = uiState.searchQuery,
                onQueryChange = { viewModel.onSearchQueryChanged(it) },
                onClearQuery = { viewModel.clearSearch() }
            )

            // Category Filter Tabs (Transformers, Circuit Breakers, Cables)
            CategoryFilterChips(
                selectedCategory = uiState.selectedCategory,
                onCategorySelect = { viewModel.onCategorySelected(it) }
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Body Content: Loading, Error, Empty, or List
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp),
                contentAlignment = Alignment.Center
            ) {
                when {
                    uiState.isLoading && uiState.assets.isEmpty() -> {
                        LoadingStateView()
                    }
                    uiState.errorMessage != null && uiState.assets.isEmpty() -> {
                        ErrorStateView(
                            message = uiState.errorMessage ?: "Unknown error",
                            onRetry = { viewModel.loadAssets(forceRefresh = true) }
                        )
                    }
                    !uiState.isLoading && uiState.assets.isEmpty() -> {
                        EmptyStateView(
                            searchQuery = uiState.searchQuery,
                            category = uiState.selectedCategory
                        )
                    }
                    else -> {
                        AssetListView(
                            assets = uiState.assets,
                            onAssetClick = onAssetClick
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun OfflineAvailabilityBanner(
    isOffline: Boolean,
    dataSource: DataSource,
    assetCount: Int,
    modifier: Modifier = Modifier
) {
    val containerColor = if (isOffline) WarningAmberContainer else SuccessGreenContainer
    val borderColor = if (isOffline) WarningAmber.copy(alpha = 0.35f) else SuccessGreenBorder
    val contentColor = if (isOffline) WarningAmber else SuccessGreen

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 6.dp),
        shape = RoundedCornerShape(14.dp),
        color = containerColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    imageVector = if (isOffline) Icons.Default.WifiOff else Icons.Default.Wifi,
                    contentDescription = null,
                    tint = contentColor,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(10.dp))
                Column {
                    Text(
                        text = if (isOffline) "Offline Mode • Encrypted Cache Active" else "Online • Cloud Sync Ready",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = contentColor
                    )
                    Text(
                        text = if (isOffline) {
                            "Assets available locally via AES-256 SQLCipher vault"
                        } else {
                            "Live data source: ${dataSource.label}"
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = contentColor.copy(alpha = 0.85f)
                    )
                }
            }

            Surface(
                shape = RoundedCornerShape(12.dp),
                color = contentColor.copy(alpha = 0.14f)
            ) {
                Text(
                    text = "$assetCount assets",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = contentColor,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                )
            }
        }
    }
}

@Composable
fun SearchBarSection(
    query: String,
    onQueryChange: (String) -> Unit,
    onClearQuery: () -> Unit,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 6.dp),
        placeholder = {
            Text(
                text = "Search by serial number (e.g., TRF-101)...",
                style = MaterialTheme.typography.bodyMedium,
                color = SlateBlue
            )
        },
        leadingIcon = {
            Icon(
                imageVector = Icons.Default.Search,
                contentDescription = "Search Icon",
                tint = ElectricBlue
            )
        },
        trailingIcon = {
            AnimatedVisibility(
                visible = query.isNotEmpty(),
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                IconButton(onClick = onClearQuery) {
                    Icon(
                        imageVector = Icons.Default.Clear,
                        contentDescription = "Clear Search",
                        tint = SlateBlue
                    )
                }
            }
        },
        singleLine = true,
        shape = RoundedCornerShape(14.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = ElectricBlue,
            unfocusedBorderColor = AppOutline,
            focusedContainerColor = Color.White,
            unfocusedContainerColor = Color.White,
            cursorColor = ElectricBlue
        )
    )
}

@Composable
fun CategoryFilterChips(
    selectedCategory: AssetCategory,
    onCategorySelect: (AssetCategory) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyRow(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(AssetCategory.entries.toTypedArray()) { category ->
            val isSelected = category == selectedCategory
            FilterChip(
                selected = isSelected,
                onClick = { onCategorySelect(category) },
                label = {
                    Text(
                        text = category.displayName,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                    )
                },
                leadingIcon = {
                    val icon = when (category) {
                        AssetCategory.TRANSFORMERS -> Icons.Default.ElectricalServices
                        AssetCategory.CIRCUIT_BREAKERS -> Icons.Default.Lock
                        AssetCategory.CABLES -> Icons.Default.Cable
                        AssetCategory.ALL -> Icons.Default.Storage
                    }
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp)
                    )
                },
                shape = RoundedCornerShape(20.dp),
                colors = FilterChipDefaults.filterChipColors(
                    containerColor = Color.White,
                    labelColor = SlateBlue,
                    iconColor = SlateBlue,
                    selectedContainerColor = ElectricBlue,
                    selectedLabelColor = Color.White,
                    selectedLeadingIconColor = Color.White
                ),
                border = FilterChipDefaults.filterChipBorder(
                    enabled = true,
                    selected = isSelected,
                    borderColor = AppOutline,
                    selectedBorderColor = ElectricBlue
                )
            )
        }
    }
}

@Composable
fun AssetListView(
    assets: List<Asset>,
    onAssetClick: (Asset) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(assets, key = { it.id }) { asset ->
            AssetCardItem(
                asset = asset,
                onClick = { onAssetClick(asset) }
            )
        }
    }
}

@Composable
fun AssetCardItem(
    asset: Asset,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color.White
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Header Row: Serial Number Badge & Category Pill
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = ElectricBlueContainer
                ) {
                    Text(
                        text = asset.serialNumber,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        color = ElectricBlue,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                    )
                }

                CategoryBadge(category = asset.category)
            }

            // Asset Name
            Text(
                text = asset.name,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = AppTextPrimary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )

            // Technical Specifications Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (asset.kvaRating != null && asset.kvaRating > 0) {
                    TechnicalChip(
                        label = "Rating",
                        value = asset.formattedKvaRating
                    )
                }

                if (asset.voltageClass != null) {
                    TechnicalChip(
                        label = "Voltage",
                        value = asset.formattedVoltageClass
                    )
                }

                if (asset.manufacturer != null) {
                    TechnicalChip(
                        label = "Maker",
                        value = asset.formattedManufacturer
                    )
                }
            }

            // Substation and Operational Status
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = asset.substationName ?: "Substation Unassigned",
                    style = MaterialTheme.typography.bodySmall,
                    color = SlateBlue
                )

                OperationalStatusBadge(status = asset.status)
            }
        }
    }
}

@Composable
fun CategoryBadge(category: AssetCategory) {
    val (bgColor, textColor) = when (category) {
        AssetCategory.TRANSFORMERS -> Color(0xFFFFF3E0) to Color(0xFFE65100)
        AssetCategory.CIRCUIT_BREAKERS -> Color(0xFFE3F2FD) to Color(0xFF1565C0)
        AssetCategory.CABLES -> Color(0xFFE8F5E9) to Color(0xFF2E7D32)
        AssetCategory.ALL -> MaterialTheme.colorScheme.surfaceVariant to SlateBlue
    }

    Surface(
        shape = RoundedCornerShape(12.dp),
        color = bgColor
    ) {
        Text(
            text = category.displayName,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = textColor,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
        )
    }
}

@Composable
fun OperationalStatusBadge(status: String) {
    val isOk = status.equals("OPERATIONAL", ignoreCase = true)
    Surface(
        shape = RoundedCornerShape(10.dp),
        color = if (isOk) SuccessGreenContainer else Color(0xFFFFEBEE)
    ) {
        Text(
            text = status.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = if (isOk) SuccessGreen else Color(0xFFC62828),
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
        )
    }
}

@Composable
fun TechnicalChip(label: String, value: String) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = SlateBlue
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.SemiBold,
            color = AppTextPrimary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
fun LoadingStateView() {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(44.dp),
            color = ElectricBlue
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "Loading Grid Assets...",
            style = MaterialTheme.typography.bodyMedium,
            color = SlateBlue
        )
    }
}

@Composable
fun EmptyStateView(searchQuery: String, category: AssetCategory) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.padding(24.dp)
    ) {
        Icon(
            imageVector = Icons.Default.Search,
            contentDescription = null,
            tint = SlateBlue,
            modifier = Modifier.size(48.dp)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = if (searchQuery.isNotBlank()) {
                "No assets match \"$searchQuery\""
            } else {
                "No assets found in ${category.displayName}"
            },
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = AppTextPrimary
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = "Try adjusting your serial number search or category filter.",
            style = MaterialTheme.typography.bodySmall,
            color = SlateBlue
        )
    }
}

@Composable
fun ErrorStateView(message: String, onRetry: () -> Unit) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
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
            text = "Unable to Retrieve Assets",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.error
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = message,
            style = MaterialTheme.typography.bodySmall,
            color = SlateBlue
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = onRetry,
            colors = ButtonDefaults.buttonColors(containerColor = ElectricBlue),
            shape = RoundedCornerShape(12.dp)
        ) {
            Icon(
                imageVector = Icons.Default.Refresh,
                contentDescription = null,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text("Retry")
        }
    }
}
