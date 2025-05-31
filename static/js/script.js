document.addEventListener("DOMContentLoaded", function () {

    var userLang = navigator.language;
    if (userLang.split("-")[0] === "es"){
        fetch("static/translate.json")
        .then(response => response.json())
        .then(data => {
          // Replace text content with translations
          document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            if (data[key]) {
              element.textContent = data[key];
            }
          });
        })
    }


    const buttonFile = document.getElementById("button-file");
    const getStatsButton1 = document.getElementById("get-stats-button1");
    const getStatsButton2 = document.getElementById("get-stats-button2");
    const getStatsButton3 = document.getElementById("get-stats-button3");
    const getStatsButton4 = document.getElementById("get-stats-button4");
    const getStatsButton5 = document.getElementById("get-stats-button5");
    const getStatsButton6 = document.getElementById("get-stats-button6");
    const imageStats = document.getElementById("statsContainer");
    const graphs1 = document.getElementById("graphs1");
    const graphs2 = document.getElementById("graphs2");
    const graphs3 = document.getElementById("graphs3");
    const graphs4 = document.getElementById("graphs4");
    const graphs5 = document.getElementById("graphs5");
    const graphs6 = document.getElementById("graphs6");
    // Add a change event listener to the "Upload File" button
    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name");
    let selectedPlatform;
    const platformButtons = document.querySelectorAll('.platform-button');

    platformButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove the 'selected' class from all buttons
            platformButtons.forEach(btn => btn.classList.remove('selected'));

            // Add the 'selected' class to the clicked button
            button.classList.add('selected');
            buttonFile.style.display = "inline-block";
            // You can now access the selected platform using button.textContent
            selectedPlatform = button.textContent;
            console.log(`Selected platform: ${selectedPlatform}`);
        });
    });

    fileInput.addEventListener("change", function () {
        const selectedFile = fileInput.files[0];
        if (selectedFile) {
            fileNameDisplay.textContent = "Selected File: " + selectedFile.name;
            fileNameDisplay.style.display = "block";
            imageStats.style.display = "block";
            const loader = document.getElementById("loader1");
            loader.style.display = "block";
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            fetch(`/numbers/${selectedPlatform}`, {
                method: "POST",
                body: formData
            }).then(response => response.json())
                .then(data => {
                    const datesInit = document.getElementById("days-init");
                    const datesEnd = document.getElementById("days-end");
                    const msgs = document.getElementById("total-msg");
                    loader.style.display = "none";
                    datesInit.innerHTML = "Starting Date: " + data["first"];
                    datesEnd.innerHTML = "Ending Date: " + data["last"];
                    msgs.innerHTML = "Total Messages Analyzed: " + data["len"];
                    graphs1.style.display = "block";
                    getStatsButton1.style.display = "inline-block";
                });
        } else {
            fileNameDisplay.textContent = "";
            fileNameDisplay.style.display = "none";
            getStatsButton1.style.display = "none";
        }
    });

    // First Button
    getStatsButton1.addEventListener("click", function () {
        // Handle the action you want to perform when the user clicks "Get Stats"
        //alert("Getting WhatsApp Stats...");
        const loader = document.getElementById("loader2");
        const error_msg = document.getElementById("error-fetch1");
        error_msg.style.display = "none";
        loader.style.display = "block";
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        fetch(`/hours/${selectedPlatform}`, {
            method: "POST",
            body: formData
        }).then(response => {
            if (!response.ok){
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const image = document.getElementById('image1');
                loader.style.display = "none";
                image.src = url;
                image.style.display = "block";
                getStatsButton1.style.display = "none";
                graphs2.style.display = "block";
                getStatsButton2.style.display = "inline-block";
                error_msg.style.display = "none";
            }).catch(error => {
                loader.style.display = "none";
                error_msg.style.display = "block";
                graphs2.style.display = "block";
                getStatsButton2.style.display = "inline-block";
                console.error('Error fetching data:', error);
        });
    });

    // Second Button
    getStatsButton2.addEventListener("click", function () {
        // Handle the action you want to perform when the user clicks "Get Stats"
        //alert("Getting WhatsApp Stats...");
        const loader = document.getElementById("loader3");
        const error_msg = document.getElementById("error-fetch2");
        loader.style.display = "block";
        error_msg.style.display = "none";
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        fetch(`/months/${selectedPlatform}`, {
            method: "POST",
            body: formData
        }).then(response => {
            if (!response.ok){
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const image = document.getElementById('image2');
                image.src = url;
                loader.style.display = "none";
                image.style.display = "block";
                getStatsButton2.style.display = "none";
                graphs3.style.display = "block";
                getStatsButton3.style.display = "inline-block";
                error_msg.style.display = "none";
            }).catch(error => {
                loader.style.display = "none";
                error_msg.style.display = "block";
                graphs3.style.display = "block";
                getStatsButton3.style.display = "inline-block";
                console.error('Error fetching data:', error);
        });
    });

    // Third Button
    getStatsButton3.addEventListener("click", function () {
        // Handle the action you want to perform when the user clicks "Get Stats"
        //alert("Getting WhatsApp Stats...");
        const loader = document.getElementById("loader4");
        const error_msg = document.getElementById("error-fetch3");
        loader.style.display = "block";
        error_msg.style.display = "none";
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        fetch(`/dayDist/${selectedPlatform}`, {
            method: "POST",
            body: formData
        }).then(response => {
            if (!response.ok){
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const image = document.getElementById('image3');
                image.src = url;
                loader.style.display = "none";
                image.style.display = "block";
                getStatsButton3.style.display = "none";
                graphs4.style.display = "block";
                getStatsButton4.style.display = "inline-block";
                error_msg.style.display = "none";
            }).catch(error => {
                loader.style.display = "none";
                error_msg.style.display = "block";
                graphs4.style.display = "block";
                getStatsButton4.style.display = "inline-block";
                console.error('Error fetching data:', error);
        });
    });

    // Forth Button
    getStatsButton4.addEventListener("click", function () {
        // Handle the action you want to perform when the user clicks "Get Stats"
        //alert("Getting WhatsApp Stats...");
        const loader = document.getElementById("loader5");
        const error_msg = document.getElementById("error-fetch4");
        loader.style.display = "block";
        error_msg.style.display = "none";
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        fetch(`/eachPerson/${selectedPlatform}`, {
            method: "POST",
            body: formData
        }).then(response => {
            if (!response.ok){
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const image = document.getElementById('image4');
                image.src = url;
                loader.style.display = "none";
                image.style.display = "block";
                getStatsButton4.style.display = "none";
                graphs5.style.display = "block";
                getStatsButton5.style.display = "inline-block";
                error_msg.style.display = "none";
            }).catch(error => {
                loader.style.display = "none";
                error_msg.style.display = "block";
                graphs5.style.display = "block";
                getStatsButton5.style.display = "inline-block";
                console.error('Error fetching data:', error);
        });
    });

    // Fifth Button
    getStatsButton5.addEventListener("click", function () {
        // Handle the action you want to perform when the user clicks "Get Stats"
        //alert("Getting WhatsApp Stats...");
        const loader = document.getElementById("loader6");
        const error_msg = document.getElementById("error-fetch5");
        loader.style.display = "block";
        error_msg.style.display = "none";
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        fetch(`/noMess/${selectedPlatform}`, {
            method: "POST",
            body: formData
        }).then(response => {
            if (!response.ok){
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const image = document.getElementById('image5');
                image.src = url;
                loader.style.display = "none";
                image.style.display = "block";
                getStatsButton5.style.display = "none";
                graphs6.style.display = "block";
                getStatsButton6.style.display = "inline-block";
                error_msg.style.display = "none";
            }).catch(error => {
                loader.style.display = "none";
                error_msg.style.display = "block";
                graphs6.style.display = "block";
                getStatsButton6.style.display = "inline-block";
                console.error('Error fetching data:', error);
        });
    });

    //Sixth Button
    getStatsButton6.addEventListener("click", function () {
        // Handle the action you want to perform when the user clicks "Get Stats"
        //alert("Getting WhatsApp Stats...");
        const loader = document.getElementById("loader7");
        const error_msg = document.getElementById("error-fetch6");
        loader.style.display = "block";
        error_msg.style.display = "none";
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        fetch(`/streak/${selectedPlatform}`, {
            method: "POST",
            body: formData
        }).then(response => {
            if (!response.ok){
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const image = document.getElementById('image6');
                image.src = url;
                loader.style.display = "none";
                image.style.display = "block";
                getStatsButton6.style.display = "none";
                showShareButton();
            }).catch(error => {
                loader.style.display = "none";
                error_msg.style.display = "block";
                console.error('Error fetching data:', error);
        });
    });
});

// Show share button when all graphs are loaded
function showShareButton() {
    const allGraphsLoaded = document.querySelectorAll('.images-show').length === 6;
    if (allGraphsLoaded) {
        document.getElementById('share').style.display = 'block';
    }
}

