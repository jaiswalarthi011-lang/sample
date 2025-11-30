let currentResearchData = null;
let currentCompanyName = '';
let currentAudio = null;
let currentInsightText = '';

document.addEventListener('DOMContentLoaded', () => {
    checkMongoStatus();

    document.getElementById('companyInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    loadApiKeys();

    // Start in search mode
    document.querySelector('.main-content').classList.add('search-mode');
});

async function checkMongoStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        const statusBadge = document.getElementById('mongoStatus');
        if (data.mongodb) {
            statusBadge.classList.add('connected');
            statusBadge.classList.remove('disconnected');
        } else {
            statusBadge.classList.add('disconnected');
            statusBadge.classList.remove('connected');
        }

        // Update TTS status indicator
        updateTTSStatus(data.tts);
    } catch (e) {
        console.error('Status check failed:', e);
    }
}

function updateTTSStatus(ttsStatus) {
    const ttsIndicator = document.getElementById('ttsStatus');
    if (!ttsIndicator) return;

    if (ttsStatus.available) {
        ttsIndicator.classList.add('connected');
        ttsIndicator.classList.remove('disconnected');
        ttsIndicator.title = 'TTS Available';
    } else {
        ttsIndicator.classList.add('disconnected');
        ttsIndicator.classList.remove('connected');
        ttsIndicator.title = ttsStatus.error || 'TTS Unavailable';
    }
}

async function performSearch() {
    const input = document.getElementById('companyInput');
    const companyName = input.value.trim();

    if (!companyName) {
        showToast('Please enter a company name', 'error');
        return;
    }

    currentCompanyName = companyName;

    // Clear everything and show loading animation
    document.getElementById('searchContainer').style.display = 'none';
    d3.select('#knowledgeGraph').classed('active', false);
    document.getElementById('sidebarLeft').classList.remove('active');
    document.getElementById('sidebarLeft').classList.add('hidden');
    document.getElementById('sidebarRight').classList.remove('active');
    document.getElementById('ceo-footer').classList.remove('active');
    document.getElementById('graphCanvas').classList.remove('full-width');

    showLoading(true);
    await startStepProgress();

    try {
        // Step 1: Analyzing Company Data
        updateStepProgress(1, 100);
        await delay(800);

        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_name: companyName })
        });

        const data = await response.json();

        if (response.ok) {
            currentResearchData = data;

            // Step 2: Research Intelligence
            updateStepProgress(2, 100);
            await delay(1000);

            // Step 3: LTIMindtree Strategy
            updateStepProgress(3, 100);
            await delay(1200);

            // Step 4: Knowledge Graph
            updateStepProgress(4, 100);
            await delay(800);

            // Step 5: Finalizing Results
            updateStepProgress(5, 100);
            await delay(1500);

            // Hide loading and show results
            showLoading(false);

            // Switch to research mode and show all components
            document.querySelector('.main-content').classList.remove('search-mode');
            document.getElementById('backBtn').classList.add('active');

            // Show sidebars and footer
            document.getElementById('sidebarLeft').classList.remove('hidden');
            document.getElementById('sidebarLeft').classList.add('active');
            document.getElementById('sidebarRight').classList.add('active');
            document.getElementById('ceo-footer').classList.add('active');
            document.getElementById('graphCanvas').classList.add('full-width');

            renderKnowledgeGraph(data);
            loadHistory();
            showToast(`Research complete for ${companyName}`, 'success');
        } else {
            showLoading(false);
            // Show search container again on error
            document.getElementById('searchContainer').style.display = 'flex';
            showToast(data.error || 'Search failed', 'error');
        }
    } catch (e) {
        console.error('Search error:', e);
        showLoading(false);
        // Show search container again on error
        document.getElementById('searchContainer').style.display = 'flex';
        showToast('Search failed. Please try again.', 'error');
    }
}

async function startStepProgress() {
    // Reset all progress bars
    for (let i = 1; i <= 5; i++) {
        const progressBar = document.getElementById(`progress${i}`);
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.classList.remove('active');
        }
    }
}

function updateStepProgress(stepNumber, percentage) {
    const progressBar = document.getElementById(`progress${stepNumber}`);
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.classList.add('active');
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function searchCompany(companyName) {
    document.getElementById('companyInput').value = companyName;
    performSearch();
}

function renderKnowledgeGraph(data) {
    const svg = d3.select('#knowledgeGraph');
    svg.selectAll('*').remove();
    svg.classed('active', true);

    const container = document.getElementById('graphCanvas');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Ensure SVG takes full container size and is centered
    svg.attr('width', '100%')
       .attr('height', '100%')
       .attr('viewBox', `0 0 ${width} ${height}`)
       .attr('preserveAspectRatio', 'xMidYMid meet');
    
    const categories = Object.keys(data.categories);
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;
    
    const nodes = [{
        id: 'center',
        name: data.company_name,
        x: centerX,
        y: centerY,
        isCenter: true
    }];
    
    const categoryColors = {
        overview: '#7C3AED',
        news: '#EC4899',
        financials: '#10B981',
        hiring: '#F59E0B',
        technology: '#3B82F6',
        acquisitions: '#8B5CF6',
        competitors: '#EF4444',
        challenges: '#6366F1'
    };
    
    categories.forEach((category, i) => {
        const angle = (i * 2 * Math.PI / categories.length) - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        nodes.push({
            id: category,
            name: category.charAt(0).toUpperCase() + category.slice(1),
            x: x,
            y: y,
            isCenter: false,
            color: categoryColors[category] || '#7C3AED',
            data: data.categories[category]
        });
    });
    
    const defs = svg.append('defs');
    
    nodes.forEach(node => {
        if (!node.isCenter) {
            const gradient = defs.append('linearGradient')
                .attr('id', `gradient-${node.id}`)
                .attr('x1', '0%')
                .attr('y1', '0%')
                .attr('x2', '100%')
                .attr('y2', '100%');
            
            gradient.append('stop')
                .attr('offset', '0%')
                .attr('stop-color', node.color)
                .attr('stop-opacity', 0.1);
            
            gradient.append('stop')
                .attr('offset', '100%')
                .attr('stop-color', node.color)
                .attr('stop-opacity', 0.3);
        }
    });
    
    const linksGroup = svg.append('g').attr('class', 'links');
    
    nodes.slice(1).forEach((node, i) => {
        const nextNode = nodes[(i + 2) % (nodes.length - 1) + 1];
        
        linksGroup.append('path')
            .attr('class', 'link-path')
            .attr('d', `M ${nodes[0].x} ${nodes[0].y} Q ${(nodes[0].x + node.x) / 2} ${(nodes[0].y + node.y) / 2 - 30} ${node.x} ${node.y}`)
            .style('stroke', node.color)
            .style('stroke-opacity', 0.3);
        
        linksGroup.append('path')
            .attr('class', 'link-path dna-link')
            .attr('d', () => {
                const midX = (node.x + nextNode.x) / 2;
                const midY = (node.y + nextNode.y) / 2;
                const controlOffset = 40;
                return `M ${node.x} ${node.y} Q ${midX} ${midY - controlOffset} ${nextNode.x} ${nextNode.y}`;
            })
            .style('stroke', node.color)
            .style('stroke-opacity', 0.2)
            .style('stroke-dasharray', '5,5');
    });
    
    const nodesGroup = svg.append('g').attr('class', 'nodes');
    
    const centerNode = nodesGroup.append('g')
        .attr('class', 'center-node')
        .attr('transform', `translate(${centerX}, ${centerY})`);
    
    centerNode.append('circle')
        .attr('r', 50)
        .attr('fill', '#000000')
        .attr('stroke', '#7C3AED')
        .attr('stroke-width', 4);
    
    const companyWords = data.company_name.split(' ');
    if (companyWords.length > 1) {
        centerNode.append('text')
            .attr('y', -8)
            .attr('fill', 'white')
            .attr('text-anchor', 'middle')
            .attr('font-size', '14px')
            .attr('font-weight', '700')
            .text(companyWords[0]);
        centerNode.append('text')
            .attr('y', 10)
            .attr('fill', 'white')
            .attr('text-anchor', 'middle')
            .attr('font-size', '14px')
            .attr('font-weight', '700')
            .text(companyWords.slice(1).join(' '));
    } else {
        centerNode.append('text')
            .attr('y', 5)
            .attr('fill', 'white')
            .attr('text-anchor', 'middle')
            .attr('font-size', '14px')
            .attr('font-weight', '700')
            .text(data.company_name);
    }
    
    nodes.slice(1).forEach(node => {
        const nodeGroup = nodesGroup.append('g')
            .attr('class', 'node-circle')
            .attr('transform', `translate(${node.x}, ${node.y})`)
            .style('cursor', 'pointer')
            .on('click', () => showInsight(node));
        
        nodeGroup.append('circle')
            .attr('r', 40)
            .attr('fill', `url(#gradient-${node.id})`)
            .attr('stroke', node.color)
            .attr('stroke-width', 3);
        
        nodeGroup.append('text')
            .attr('class', 'node-label')
            .attr('y', 60)
            .attr('fill', '#000000')
            .text(node.name);
        
        const iconGroup = nodeGroup.append('g')
            .attr('transform', 'translate(-12, -12)');
        
        const icons = {
            overview: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
            news: '<path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1m2 13a2 2 0 0 1-2-2V7m2 13a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2m-4-3H9M7 16h6M7 12h6"/>',
            financials: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
            hiring: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
            technology: '<rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
            acquisitions: '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M11 18H8a2 2 0 0 1-2-2V9"/>',
            competitors: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
            challenges: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
        };
        
        iconGroup.append('g')
            .attr('transform', 'translate(0, 0)')
            .html(`<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="${node.color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${icons[node.id] || icons.overview}</svg>`);
    });
}

async function showInsight(node) {
    const panel = document.getElementById('sidebarRight');
    const category = document.getElementById('insightCategory');
    const badge = document.getElementById('insightBadge');
    const content = document.getElementById('insightContent');
    const transcript = document.getElementById('ttsTranscript');

    category.textContent = node.name;
    badge.textContent = 'Analyzing...';

    // Show loading state in panel
    content.innerHTML = '<div class="insight-loading"><div class="loading-spinner"></div><p>Generating insights...</p></div>';

    transcript.textContent = 'Preparing audio...';
    currentInsightText = '';

    panel.classList.add('active');

    try {
        // Generate insights for the panel using Grok
        const response = await fetch(`/api/panel-insight/${node.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                insights: node.data.insights,
                company_name: currentCompanyName,
                category: node.id
            })
        });

        const data = await response.json();

        if (data.insight) {
            // Create tabbed interface: LTIMindtree Opportunity first, then Research Data
            let html = `
                <div class="panel-tabs">
                    <div class="tab-buttons">
                        <button class="tab-btn active" onclick="switchTab('opportunity')">LTIMindtree Opportunity</button>
                        <button class="tab-btn" onclick="switchTab('research')">Research Data</button>
                    </div>
                    <div class="tab-content">
                        <div id="opportunity-tab" class="tab-panel active">
                            <div class="processed-insight">
                                <div class="insight-highlight">
                                    <p>${data.insight}</p>
                                </div>
                            </div>
                        </div>
                        <div id="research-tab" class="tab-panel">
                            <div class="research-data-section">
            `;

            // Show original research data in second tab
            if (node.data.insights && node.data.insights.length > 0) {
                node.data.insights.forEach(insight => {
                    html += `
                        <div class="insight-item">
                            <h5>${insight.title}</h5>
                            <p>${insight.snippet}</p>
                        </div>
                    `;
                });
            }

            html += `
                            </div>
                        </div>
                    </div>
                </div>
            `;

            content.innerHTML = html;
            badge.textContent = `${node.data.insights.length} Research Items + 1 Opportunity`;

            // Use ultra-short TTS version for audio (show full text, play condensed version)
            currentInsightText = await getUltraShortTTS(data.insight, currentCompanyName, node.id);
            // Auto-play the condensed audio
            await playInsight();
        } else {
            // Fallback to raw data if Grok fails
            badge.textContent = `${node.data.insights.length} insights`;
            let html = '';
            if (node.data.insights && node.data.insights.length > 0) {
                node.data.insights.forEach(insight => {
                    html += `
                        <div class="insight-item">
                            <h4>${insight.title}</h4>
                            <p>${insight.snippet}</p>
                        </div>
                    `;
                });
            } else {
                html = '<p>No insights available for this category.</p>';
            }
            content.innerHTML = html;
            transcript.textContent = 'Failed to generate audio insight';
        }
    } catch (e) {
        console.error('Failed to generate insight:', e);
        // Fallback to raw data
        badge.textContent = `${node.data.insights.length} insights`;
        let html = '';
        if (node.data.insights && node.data.insights.length > 0) {
            node.data.insights.forEach(insight => {
                html += `
                    <div class="insight-item">
                        <h4>${insight.title}</h4>
                        <p>${insight.snippet}</p>
                    </div>
                `;
            });
        } else {
            html = '<p>No insights available for this category.</p>';
        }
        content.innerHTML = html;
        transcript.textContent = 'Failed to load audio';
    }
}

function closeInsightPanel() {
    document.getElementById('sidebarRight').classList.remove('active');
    stopAudio();
}

function switchTab(tabName) {
    // Switch between opportunity and research tabs
    const opportunityTab = document.getElementById('opportunity-tab');
    const researchTab = document.getElementById('research-tab');
    const opportunityBtn = document.querySelector('.tab-btn[onclick*="opportunity"]');
    const researchBtn = document.querySelector('.tab-btn[onclick*="research"]');

    if (tabName === 'opportunity') {
        opportunityTab.classList.add('active');
        researchTab.classList.remove('active');
        opportunityBtn.classList.add('active');
        researchBtn.classList.remove('active');
    } else {
        researchTab.classList.add('active');
        opportunityTab.classList.remove('active');
        researchBtn.classList.add('active');
        opportunityBtn.classList.remove('active');
    }
}

async function getUltraShortTTS(fullInsight, companyName, category) {
    try {
        const response = await fetch('/api/ultra-short-tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                insight: fullInsight,
                company_name: companyName,
                category: category
            })
        });
        const data = await response.json();
        return data.tts_text || `${companyName} benefits from LTIMindtree solutions.`;
    } catch (e) {
        console.error('Ultra-short TTS error:', e);
        return `${companyName} benefits from LTIMindtree solutions.`;
    }
}

async function playInsight() {
    const progressBar = document.getElementById('ttsProgressBar');
    const transcript = document.getElementById('ttsTranscript');

    // Stop and cleanup any existing audio
    stopAudio();

    if (!currentInsightText) {
        showToast('No insight text available', 'error');
        return;
    }

    transcript.textContent = 'Preparing audio...';

    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: currentInsightText })
        });

        const data = await response.json();

        if (data.audio) {
            const audioBlob = base64ToBlob(data.audio, 'audio/mp3');
            const audioUrl = URL.createObjectURL(audioBlob);

            // Create fresh audio element
            currentAudio = new Audio(audioUrl);

            // Simple event handlers
            currentAudio.onloadeddata = () => {
                transcript.textContent = 'Playing audio...';
                startCeoSpeaking();
            };

            currentAudio.ontimeupdate = () => {
                if (currentAudio.duration > 0) {
                    const progress = (currentAudio.currentTime / currentAudio.duration) * 100;
                    progressBar.style.width = `${progress}%`;
                }
            };

            currentAudio.onended = () => {
                progressBar.style.width = '0%';
                transcript.textContent = 'Audio complete';
                setTimeout(() => {
                    transcript.textContent = '';
                }, 2000);
                stopCeoSpeaking();
                // Clean up
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
            };

            currentAudio.onerror = () => {
                showToast('Audio playback failed', 'error');
                transcript.textContent = 'Audio error';
                stopCeoSpeaking();
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
            };

            // Start playing
            currentAudio.play().catch(() => {
                showToast('Failed to start audio', 'error');
                transcript.textContent = 'Playback failed';
            });

        } else {
            throw new Error(data.error || 'TTS failed');
        }
    } catch (e) {
        console.error('TTS error:', e);
        showToast('Failed to load audio', 'error');
        transcript.textContent = 'Failed to load audio';
    }
}

function stopAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }
    document.getElementById('ttsProgressBar').style.width = '0%';

    // Stop CEO speaking animation
    stopCeoSpeaking();
}

function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

function openApiModal() {
    document.getElementById('apiModal').classList.add('active');
    loadApiKeys();
}

function closeApiModal() {
    document.getElementById('apiModal').classList.remove('active');
}

async function loadApiKeys() {
    try {
        const response = await fetch('/api/keys');
        const keys = await response.json();
        
        document.getElementById('serperKey').placeholder = keys.serper || 'Enter key...';
        document.getElementById('openrouterKey').placeholder = keys.openrouter || 'Enter key...';
        document.getElementById('cartesiaKey').placeholder = keys.cartesia || 'Enter key...';
        document.getElementById('deepgramKey').placeholder = keys.deepgram || 'Enter key...';
        document.getElementById('firecrawlKey').placeholder = keys.firecrawl || 'Enter key...';
        document.getElementById('sonarKey').placeholder = keys.sonar || 'Enter key...';
    } catch (e) {
        console.error('Failed to load API keys:', e);
    }
}

async function saveApiKeys() {
    const keys = {
        serper: document.getElementById('serperKey').value,
        openrouter: document.getElementById('openrouterKey').value,
        cartesia: document.getElementById('cartesiaKey').value,
        deepgram: document.getElementById('deepgramKey').value,
        firecrawl: document.getElementById('firecrawlKey').value,
        sonar: document.getElementById('sonarKey').value
    };
    
    const filteredKeys = {};
    for (const [key, value] of Object.entries(keys)) {
        if (value) filteredKeys[key] = value;
    }
    
    if (Object.keys(filteredKeys).length === 0) {
        showToast('No keys to update', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filteredKeys)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('API keys updated successfully', 'success');
            closeApiModal();
            
            document.getElementById('serperKey').value = '';
            document.getElementById('openrouterKey').value = '';
            document.getElementById('cartesiaKey').value = '';
            document.getElementById('deepgramKey').value = '';
            document.getElementById('firecrawlKey').value = '';
            document.getElementById('sonarKey').value = '';
        } else {
            showToast(data.error || 'Failed to update keys', 'error');
        }
    } catch (e) {
        console.error('Save keys error:', e);
        showToast('Failed to save API keys', 'error');
    }
}

function toggleKeyVisibility(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();

        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        // Group history items and add dividers
        let previousCompany = null;

        history.forEach((item, index) => {
            const currentCompany = item.company_name.toLowerCase();

            // Add divider if company changes (but not for the first item)
            if (previousCompany && previousCompany !== currentCompany && index > 0) {
                const divider = document.createElement('div');
                divider.className = 'history-divider';
                historyList.appendChild(divider);
            }

            const div = document.createElement('div');
            div.className = 'history-item';
            div.onclick = () => searchCompany(item.company_name);

            // Generate company icon (first 1-2 letters)
            const companyWords = item.company_name.split(' ');
            let iconText = companyWords[0].charAt(0).toUpperCase();
            if (companyWords.length > 1) {
                iconText += companyWords[1].charAt(0).toUpperCase();
            }

            // Format timestamp
            const timestamp = new Date(item.timestamp);
            const timeString = timestamp.toLocaleDateString() + ' ' + timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

            div.innerHTML = `
                <div class="history-item-content">
                    <div class="company-icon">${iconText}</div>
                    <div class="company-details">
                        <div class="company-name">${item.company_name}</div>
                        <div class="company-time">${timeString}</div>
                    </div>
                </div>
                <button class="delete-btn" onclick="event.stopPropagation(); deleteHistory('${item.company_name}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            `;

            historyList.appendChild(div);
            previousCompany = currentCompany;
        });
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

async function deleteHistory(companyName) {
    try {
        await fetch(`/api/history/${encodeURIComponent(companyName)}`, {
            method: 'DELETE'
        });
        loadHistory();
        showToast('History item deleted', 'success');
    } catch (e) {
        console.error('Delete history error:', e);
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function goBack() {
    // Hide everything except navbar and search - create a clean slate
    document.getElementById('searchContainer').style.display = 'flex';
    d3.select('#knowledgeGraph').classed('active', false);
    document.getElementById('backBtn').classList.remove('active');

    // Switch back to search mode
    document.querySelector('.main-content').classList.add('search-mode');

    // Hide all research-related elements completely
    document.getElementById('sidebarLeft').classList.remove('active');
    document.getElementById('sidebarLeft').classList.add('hidden');
    document.getElementById('sidebarRight').classList.remove('active');
    document.getElementById('ceo-footer').classList.remove('active');
    document.getElementById('graphCanvas').classList.remove('full-width');

    // Clear any research data and UI state
    closeInsightPanel();
    stopAudio();
    currentResearchData = null;
    currentCompanyName = '';

    // Clear search input for fresh start
    document.getElementById('companyInput').value = '';

    // Clear any background particles
    const particles = document.querySelectorAll('.background-particle');
    particles.forEach(particle => {
        if (particle.parentNode) {
            particle.parentNode.removeChild(particle);
        }
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function startCeoSpeaking() {
    const ceoAvatar = document.getElementById('ceoAvatar');
    const particlesContainer = document.getElementById('ceoParticles');

    ceoAvatar.classList.add('speaking');

    // Create tons of floating violet particles
    for (let i = 0; i < 20; i++) {
        setTimeout(() => {
            const particle = document.createElement('div');
            particle.className = 'ceo-particle-large';
            particle.style.left = Math.random() * 120 + 'px';
            particle.style.top = Math.random() * 120 + 'px';
            particle.style.animationDelay = Math.random() * 2 + 's';
            particle.style.animationDuration = (Math.random() * 2 + 2) + 's';
            particlesContainer.appendChild(particle);

            // Remove particle after animation
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            }, 4000);
        }, i * 100);
    }

    // Add background particle effects
    createBackgroundParticles();
}

function stopCeoSpeaking() {
    const ceoAvatar = document.getElementById('ceoAvatar');
    ceoAvatar.classList.remove('speaking');
}

function createBackgroundParticles() {
    // Create floating background particles during CEO speaking
    const body = document.body;

    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.className = 'background-particle';
        particle.style.cssText = `
            position: fixed;
            width: ${Math.random() * 6 + 2}px;
            height: ${Math.random() * 6 + 2}px;
            background: ${Math.random() > 0.5 ? 'var(--primary-violet)' : '#a855f7'};
            border-radius: 50%;
            opacity: 0;
            z-index: 1;
            pointer-events: none;
            left: ${Math.random() * 100}vw;
            top: ${Math.random() * 100}vh;
            animation: backgroundParticleFloat ${Math.random() * 3 + 4}s ease-in-out infinite;
            animation-delay: ${Math.random() * 2}s;
        `;
        body.appendChild(particle);

        // Remove after animation
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, 6000);
    }
}
