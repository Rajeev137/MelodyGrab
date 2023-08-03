const form = document.getElementById('form');
const url = document.getElementById('input_link');

form.addEventListener('submit' , function(event) {

    event.preventDefault();
    const urlInput = document.getElementById("url");
    fetch('validate-url', {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: urlInput }),
    })
    .then(response = response.json())
    .then (data => {
        if(data.valid){
            window.location.href = "endpage.html";

        }
        else {
            errorMessage.innerText = "Invalid Spotify URL.";
            errorMessage.style.display = "block";
        }
    })
    .catch(error => {
        console.error("Error: ", error);
    })

});

