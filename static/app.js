document.addEventListener('DOMContentLoaded', function() {
    const promptInput = document.getElementById('prompt-input');
    const charCount = document.getElementById('char-count');
    const personaSelect = document.getElementById('persona-select');
    const personaDescription = document.getElementById('persona-description');
    const customPromptSection = document.getElementById('custom-prompt-section');
    const customPrompt = document.getElementById('custom-prompt');
    const useRagie = document.getElementById('use-ragie');
    const ragieQuerySection = document.getElementById('ragie-query-section');
    const ragieQuery = document.getElementById('ragie-query');
    const temperature = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    const maxTokens = document.getElementById('max-tokens');
    const tokensValue = document.getElementById('tokens-value');
    const generateBtn = document.getElementById('generate-btn');
    const copyBtn = document.getElementById('copy-btn');
    const critiqueBtn = document.getElementById('critique-btn');
    const closeCritique = document.getElementById('close-critique');
    const refineBtn = document.getElementById('refine-btn');
    
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const loadingMessage = document.getElementById('loading-message');
    const generatedContent = document.getElementById('generated-content');
    const contentText = document.getElementById('content-text');
    const contentMeta = document.getElementById('content-meta');
    const outputActions = document.getElementById('output-actions');
    const critiqueSection = document.getElementById('critique-section');
    const critiqueContent = document.getElementById('critique-content');
    
    const toastContainer = document.getElementById('toast-container');
    
    let currentContent = '';
    let currentCritique = '';
    let originalPrompt = '';

    const personaDescriptions = {
        'professional_writer': 'A skilled professional writer with expertise in clear, engaging content',
        'technical_expert': 'A technical writer specializing in documentation and explanations',
        'creative_storyteller': 'A creative writer with a flair for narrative and storytelling',
        'business_consultant': 'A business communication expert focused on professional messaging',
        'educator': 'An experienced teacher skilled at explaining concepts clearly',
        'marketing_specialist': 'A marketing expert focused on persuasive, compelling content',
        'custom': 'Define your own custom persona with specific instructions'
    };

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function showLoading(message = 'Processing...') {
        emptyState.style.display = 'none';
        generatedContent.style.display = 'none';
        loadingState.style.display = 'flex';
        loadingMessage.textContent = message;
        generateBtn.disabled = true;
    }

    function hideLoading() {
        loadingState.style.display = 'none';
        generateBtn.disabled = false;
    }

    function showContent(content, usage = null) {
        hideLoading();
        emptyState.style.display = 'none';
        generatedContent.style.display = 'block';
        outputActions.style.display = 'flex';
        contentText.textContent = content;
        currentContent = content;
        
        if (usage) {
            contentMeta.innerHTML = `
                <span>Tokens used: ${usage.total_tokens}</span>
                <span style="margin-left: 1rem;">Prompt: ${usage.prompt_tokens} | Completion: ${usage.completion_tokens}</span>
            `;
        }
    }

    promptInput.addEventListener('input', function() {
        charCount.textContent = this.value.length;
    });

    personaSelect.addEventListener('change', function() {
        const selectedPersona = this.value;
        personaDescription.textContent = personaDescriptions[selectedPersona] || '';
        
        if (selectedPersona === 'custom') {
            customPromptSection.style.display = 'block';
        } else {
            customPromptSection.style.display = 'none';
        }
    });

    useRagie.addEventListener('change', function() {
        ragieQuerySection.style.display = this.checked ? 'block' : 'none';
    });

    temperature.addEventListener('input', function() {
        tempValue.textContent = this.value;
    });

    maxTokens.addEventListener('input', function() {
        tokensValue.textContent = this.value;
    });

    generateBtn.addEventListener('click', async function() {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            showToast('Please enter a prompt', 'warning');
            return;
        }

        originalPrompt = prompt;
        showLoading('Generating content...');
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    persona: personaSelect.value,
                    custom_prompt: customPrompt.value,
                    use_ragie: useRagie.checked,
                    ragie_query: ragieQuery.value || prompt,
                    temperature: parseFloat(temperature.value),
                    max_tokens: parseInt(maxTokens.value)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                showContent(data.content, data.usage);
                if (data.context_used) {
                    showToast('Content generated with knowledge base context', 'success');
                } else {
                    showToast('Content generated successfully', 'success');
                }
            } else {
                hideLoading();
                showToast(data.error || 'Generation failed', 'error');
            }
        } catch (error) {
            hideLoading();
            showToast('An error occurred: ' + error.message, 'error');
        }
    });

    copyBtn.addEventListener('click', async function() {
        try {
            await navigator.clipboard.writeText(currentContent);
            showToast('Copied to clipboard', 'success');
        } catch (error) {
            showToast('Failed to copy', 'error');
        }
    });

    critiqueBtn.addEventListener('click', async function() {
        if (!currentContent) {
            showToast('No content to critique', 'warning');
            return;
        }

        critiqueBtn.disabled = true;
        critiqueContent.innerHTML = '<div class="spinner" style="margin: 2rem auto;"></div>';
        critiqueSection.style.display = 'block';
        
        try {
            const response = await fetch('/api/critique', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: currentContent,
                    original_prompt: originalPrompt
                })
            });

            const data = await response.json();
            
            if (data.success) {
                critiqueContent.textContent = data.critique;
                currentCritique = data.critique;
                showToast('Critique generated', 'success');
            } else {
                critiqueContent.textContent = 'Failed to generate critique: ' + (data.error || 'Unknown error');
                showToast(data.error || 'Critique failed', 'error');
            }
        } catch (error) {
            critiqueContent.textContent = 'Error: ' + error.message;
            showToast('An error occurred', 'error');
        } finally {
            critiqueBtn.disabled = false;
        }
    });

    closeCritique.addEventListener('click', function() {
        critiqueSection.style.display = 'none';
    });

    refineBtn.addEventListener('click', async function() {
        if (!currentContent || !currentCritique) {
            showToast('No content or critique available', 'warning');
            return;
        }

        showLoading('Refining content...');
        critiqueSection.style.display = 'none';
        
        try {
            const response = await fetch('/api/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    original_content: currentContent,
                    critique: currentCritique
                })
            });

            const data = await response.json();
            
            if (data.success) {
                showContent(data.refined_content, data.usage);
                showToast('Content refined successfully', 'success');
            } else {
                hideLoading();
                showToast(data.error || 'Refinement failed', 'error');
            }
        } catch (error) {
            hideLoading();
            showToast('An error occurred: ' + error.message, 'error');
        }
    });

    feather.replace();
});
