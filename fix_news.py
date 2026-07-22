import os

path = r'c:\Users\dell\Forex News\app\app\src\main\java\com\forexnews\app\ui\news\NewsFeedScreen.kt'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's completely recreate the start of NewsFeedScreen.kt
header = '''package com.forexnews.app.ui.news

import com.forexnews.app.R

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Menu
import androidx.compose.ui.res.painterResource
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.forexnews.app.domain.model.NewsArticle
import com.forexnews.app.domain.model.NewsSentiment
import java.text.SimpleDateFormat
import java.util.*
import kotlin.math.abs

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewsFeedScreen(
    onMenuClick: () -> Unit,
    onShowProDialog: () -> Unit = {},
    viewModel: NewsFeedViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val summaries by viewModel.summaries.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()

    val filters = listOf("All", "High Impact", "USD", "EUR", "GBP", "JPY", "AUD", "CAD")

    // Load more on reaching near bottom
    LaunchedEffect(listState.firstVisibleItemIndex) {
        val totalItems = listState.layoutInfo.totalItemsCount
        val lastVisible = listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
        if (lastVisible >= totalItems - 3 && state.hasMore) {
            viewModel.loadMore()
        }
    }

    LaunchedEffect(state.error) {
        if (state.error == "AI Limit Reached. Upgrade to PRO for unlimited analysis.") {
            onShowProDialog()
            viewModel.clearError()
        }
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text("News Feed", fontWeight = FontWeight.ExtraBold,
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onBackground)
                },
                navigationIcon = {
                    IconButton(onClick = onMenuClick) {
                        Icon(painter = painterResource(id = R.drawable.ic_custom_menu), contentDescription = "Menu",
                            tint = MaterialTheme.colorScheme.onBackground)
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::refresh) {
                        Icon(Icons.Outlined.Refresh, contentDescription = "Refresh",
                            tint = MaterialTheme.colorScheme.onBackground)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
'''

# Find the padding -> and replace everything before it
idx = content.find(') { padding ->')
if idx != -1:
    idx2 = content.find('LazyColumn(', idx)
    if idx2 != -1:
        new_content = header + content[idx2:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Fixed successfully!')
    else:
        print('LazyColumn not found!')
else:
    print('padding -> not found!')
