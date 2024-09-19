// GET function
async function get() {
    let input = document.getElementById('input');
    let resultDiv = document.getElementById('result');

    try {
        const response = await fetch(`/api/movie/${input.value}`);
        const status_code = response.status;

        if (status_code === 200) {
            const movies = await response.json();
            // DEBUGING: console.log(movies);
            resultDiv.innerHTML = ''; // Clear previous results

            // Create movie card based on the response data
            const movie = {
                'title': movies['massage'][0],
                'year': movies['massage'][1],
                'vots': movies['massage'][2],
                'genres': movies['massage'][3],
                'rating': movies['massage'][4],
            };

            // Create movie card element dynamically
            let movieCard = document.createElement('div');
            movieCard.classList.add('card-project');

            movieCard.innerHTML = `
                <div class="card_Movie">
                    <div class="info_Movie">
                    <div class="Genres genres"><strong>Genres</strong>: </div>
                    <div class="watch"><strong>Watch</strong>: <span>CommingSoon!</span></div>
                    <div class="Rating"><strong>Rating</strong>: <span>${movie.rating}</span></div>
                    <div class="Votes"><strong>Votes</strong>: <span>${movie.vots}</span></div>
                    <div class="Year"><strong>Year</strong>: <span>${movie.year}</span></div>
                        <div class="name_Movie"><strong>Title</strong>: <span>${movie.title}</span></div>
                    </div>
                </div>
            `;

            // Handle genres
            let genresDiv = movieCard.querySelector('.genres');
            let genres = movie.genres.split(',');
            // set([1,1,2,3,4]) Evqvlaent in js
            const uniqueGenres = [...new Set(genres)];
            const select = document.createElement('select');
            uniqueGenres.forEach((genre) => {
                const option = document.createElement('option');
                option.innerText = genre;
                select.appendChild(option);
            });
            genresDiv.appendChild(select);

            // Append the movie card to the result div
            resultDiv.appendChild(movieCard);

        } else if (status_code === 404) {
            resultDiv.innerHTML = 'Movie Not Found';
        } else if (status_code === 500) {
            resultDiv.innerHTML = 'An Error Occurred';
        }
    } catch (error) {
        // DEBUGING: console.log("Error fetching movie data:", error);
        resultDiv.innerText = 'An Error Occurred';
    }
}

// POST function
async function post(){
    try{
        titleDoc = document.getElementById('title')
        yearDoc = document.getElementById('year')
        votsDoc = document.getElementById('vots')
        genresDoc = document.getElementById('genres')
        ratingDoc = document.getElementById('rating')
        episodesDoc = document.getElementById('episodes')
        resultDiv = document.getElementById('output')
        movieData = {
            'year': yearDoc.value,
            'votes': votsDoc.value,
            'genre': genresDoc.value,
            'rating': ratingDoc.value,
            'episodes': episodesDoc.value,
        }
        reqbody = JSON.stringify(movieData)
        console.log(reqbody)
        data = await fetch(`/api/movie/${title.value}`,
            {
                'method': 'POST',
                'headers': {
                    "Content-Type": "application/json",
                },
                'body': reqbody
            }
        );
        result = await data.json()
        const status_code = data.status
        console.log(result)
        msg = result['massage']
        // debuging
        // console.log(msg)
        if (status_code == 201){
            document.getElementById('output').innerText = msg;
        }else if(status_code == 500){
            resultDiv.innerText = msg;
        }
        }catch(error){
            // debuging
            // console.log("Error fetching movie data:", error);
            resultDiv.innerText = `An Error Occurred`;
        }
    }

// DELETE function
async function deleteMovie(){
    try{
        title = document.getElementById('title').value
        data = await fetch(`/api/movie/${title}`,
            {
                'method': 'DELETE'
            }
        );
        result = await data.json()
        status_code = data.status
        msg = result['massage']
        // DEBUGING: console.log(data)
        // DEBUGING: console.log(result)
        // DEBUGING: console.log(status_code)
        if (status_code == 202){
            document.getElementById('output').innerText = msg;
        }else if(status_code == 500){
            document.getElementById('output').innerText = msg;
        }else if(status_code == 404){
            document.getElementById('output').innerText = msg;
        }
    }catch(error){
        console.log(error)
    }
}
async function put(){
    try{
        title = document.getElementById('title').value
        rateing = document.getElementById('rateing').value
        reqbody = {
            'rating': rateing
        }
        reqbody = JSON.stringify(reqbody)
        data = await fetch(`/api/movie/${title}`,
            {
                'method': 'PUT',
                'headers': {
                    "Content-Type": "application/json",
                },
                'body': reqbody
            }
        )
        result = await data.json()
        status_code = data.status
        msg = result['massage']
        DEBUGING: console.log(data)
        DEBUGING: console.log(result)
        DEBUGING: console.log(status_code)
        if (status_code == 201){
            document.getElementById('output').innerText = msg;
        }else if (status_code == 404){
            document.getElementById('output').innerText = msg;
        }else if (status_code == 500){
            document.getElementById('output').innerText = msg;
        }
    }catch(error){
        console.log(error)
    }
    }

function Search(){
    cards = document.querySelectorAll('.cardi')
    input = document.getElementById('search').value.toLowerCase()
    let visable = 0
    cards.forEach( card => {
        title = card.getAttribute('data-title').toLowerCase()
        genre = card.getAttribute('data-genres').toLowerCase()
        // DEBUGING: console.log(`Title: ${title}\nGenre: ${genre}`)
        if (title.includes(input) || genre.includes(input)){
            card.style.display = 'block';
            visable++
        }else{
            card.style.display = 'none';
        }
        if (visable == 0){
            document.getElementById('notFoundMessage').style.display = 'block'
        }else if(visable != 0){
            document.getElementById('notFoundMessage').style.display = 'none'
        }
    })
}
function hideOrShow(){
if (document.documentElement.scrollTop > 100 || document.body.scrollTop > 50){
    document.getElementById('gotop').style.display = 'block';
}else{
    document.getElementById('gotop').style.display = 'none';
}
}

function gotop(){
    document.documentElement.scrollTo({top: 0,behavior: 'smooth'});
    document.body.scrollTo({top: 0,behavior: 'smooth'});
}