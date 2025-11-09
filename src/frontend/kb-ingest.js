function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}

function uploadFiles() {
    const fileInput = document.getElementById('file-upload');
    const statusDiv = document.getElementById('upload-status');
    const fileList = document.getElementById('file-list');

    if (fileInput.files.length === 0) {
        statusDiv.textContent = 'Please select files to upload';
        statusDiv.className = 'status-msg error';
        return;
    }

    statusDiv.textContent = 'Processing files...';
    statusDiv.className = 'status-msg';

    setTimeout(() => {
        const today = new Date().toISOString().split('T')[0];

        Array.from(fileInput.files).forEach(file => {
            const li = document.createElement('li');
            li.textContent = `${file.name} - ${today}`;
            fileList.insertBefore(li, fileList.firstChild);
        });

        statusDiv.textContent = `Successfully uploaded ${fileInput.files.length} file(s)`;
        statusDiv.className = 'status-msg success';
        fileInput.value = '';

        setTimeout(() => {
            statusDiv.textContent = '';
        }, 3000);
    }, 1500);
}

function addWebLink(event) {
    event.preventDefault();

    const urlInput = document.getElementById('web-url');
    const statusDiv = document.getElementById('web-status');
    const webList = document.getElementById('web-list');

    statusDiv.textContent = 'Crawling and processing URL...';
    statusDiv.className = 'status-msg';

    setTimeout(() => {
        const today = new Date().toISOString().split('T')[0];
        const li = document.createElement('li');
        li.textContent = `${urlInput.value} - ${today}`;
        webList.insertBefore(li, webList.firstChild);

        statusDiv.textContent = 'Successfully ingested web content';
        statusDiv.className = 'status-msg success';
        urlInput.value = '';

        setTimeout(() => {
            statusDiv.textContent = '';
        }, 3000);
    }, 2000);
}

function addText(event) {
    event.preventDefault();

    const titleInput = document.getElementById('text-title');
    const contentInput = document.getElementById('text-content');
    const statusDiv = document.getElementById('text-status');
    const textList = document.getElementById('text-list');

    statusDiv.textContent = 'Processing text entry...';
    statusDiv.className = 'status-msg';

    setTimeout(() => {
        const today = new Date().toISOString().split('T')[0];
        const li = document.createElement('li');
        li.textContent = `${titleInput.value} - ${today}`;
        textList.insertBefore(li, textList.firstChild);

        statusDiv.textContent = 'Successfully added text to knowledge base';
        statusDiv.className = 'status-msg success';
        titleInput.value = '';
        contentInput.value = '';

        setTimeout(() => {
            statusDiv.textContent = '';
        }, 3000);
    }, 1000);
}
