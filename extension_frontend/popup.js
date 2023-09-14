const badUrls = [];
const temp = [];
const url_data = [];

document.getElementById('collectButton').addEventListener('click', () => {
  // Query for the active tab
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    // Check if a valid tab is found
    if (tabs && tabs.length > 0) {
      const activeTab = tabs[0];

      // Execute the content script to collect URLs
      chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        function: () => {
          const hrefTags = Array.from(document.querySelectorAll('a')).map(a => a.href);
          console.log(hrefTags);
          return hrefTags;
        },
      }, (injectionResults) => {
        if (!chrome.runtime.lastError) {
          const urls = injectionResults[0].result;
          fetch('http://localhost:8000/collect', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls }), // Send the URLs as JSON
          })
            .then(response => response.json())
            .then(data => {
              console.log('Results from backend:', data);

              badUrls.push(...data);

              const badUrlsList = document.getElementById('badUrlsList');
              badUrlsList.innerHTML = '';

              badUrls.forEach((url, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${url}`;
                badUrlsList.appendChild(listItem);
              });

            })
            .catch(error => {
              console.error('Error:', error);
            });
        } else {
          console.error(chrome.runtime.lastError);
        }
      });
    } else {
      console.error('No active tab found.');
    }
  });
});  


// Add an event listener for the submit button
document.getElementById('submitButton').addEventListener('click', () => {
  // Get the URL input value
  const urlInput = document.getElementById('urlInput');
  const url = urlInput.value;

  // Check if the URL is not empty
  if (url.trim() !== '') {
    // Send the URL to the backend
    fetch('http://localhost:8000/collection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ urls: [url] }), // Send the URL as an array
    })
      .then(response => response.json())
      .then(data => {
        console.log('Results from backend:', data);

        temp.push(...data)

        const paragraph = document.getElementById('resdisplay');
        if(temp.length > 1){
          paragraph.textContent = 'Maybe Harmful URL';
          const button = document.createElement('button');
          button.textContent = 'Genetare Complaint';
          button.addEventListener('click', createPopup);
          function createPopup() {
          fetch('http://localhost:8000/process_url', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ urls: [url] }), // Send the URL as an array
          })
          .then(response => response.json())
          .then(data => {
            url_data.push(...data)
            const popup = window.open('', 'MyPopup', 'width=500,height=300');
            const table = popup.document.createElement('table');
            table.border = '1'; // Add a border to the table

            // Create rows for URL, Domain, IP Address, and Location
            const labels = ['URL', 'Domain Name', 'IP Address', 'Location'];

            labels.forEach((label, index) => {
              const row = popup.document.createElement('tr');

              // Create a cell for the label
              const labelCell = popup.document.createElement('td');
              labelCell.textContent = label;
              row.appendChild(labelCell);

              // Create a cell for the corresponding value from url_data
              const valueCell = popup.document.createElement('td');
              valueCell.textContent = url_data[index];
              row.appendChild(valueCell);

              // Append the row to the table
              table.appendChild(row);
            });

            // Append the table to the popup's body
            popup.document.body.appendChild(table);
            const email_button = document.createElement('button');
            email_button.textContent = 'Send Mail';
            email_button.addEventListener('click', sendmail);
            function sendmail(){
              fetch('http://localhost:8000/post_mail', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ urls: [url] }), // Send the URL as an array
                })
                .then(response => response.json())
                .then(data=>{
                  const res = []
                  res.push(...data)
                  if(res.length > 0){
                    const successMessage = popup.document.createElement('p');
                    successMessage.textContent = 'Complaint successfully generated!';
                    popup.document.body.appendChild(successMessage);
                  }
                  else{
                    const successMessage = popup.document.createElement('p');
                    successMessage.textContent = 'Failed to Send';
                    popup.document.body.appendChild(successMessage);
                  }
                  
                })
                .catch(error => {
                  console.error('Error:', error);
                });
            }
            popup.document.body.appendChild(email_button)
          })
          .catch(error => {
            console.error('Error:', error);
          });
            // Append the unordered list to the popup's bod
        }
          document.body.appendChild(button);
        }
        else{
          paragraph.textContent = 'Safe URL';
        }
        
        // Clear the URL input field
        urlInput.value = '';
      })
      .catch(error => {
        console.error('Error:', error);
      });
  } else {
    console.error('URL input is empty.');
  }
});
