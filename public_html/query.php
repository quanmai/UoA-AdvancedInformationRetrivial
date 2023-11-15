<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini Search Engine</title>
    <script defer src="https://use.fontawesome.com/releases/v5.3.1/js/all.js"></script>
    <link rel="stylesheet" href="styles.css">
</head>

<body>
    <h4></h4> 
    <nav>
        <a href="http://www.csce.uark.edu/~sgauch/5533/F23/" target="_blank">Information Retrieval</a>
        <a href="https://quanmai.github.io" target="_blank">Quan Mai</a>
        <a href="https://github.com/quanmai/UoA-AdvancedInformationRetrivial" target="_blank"><i class="fab fa-lg fa-github"></i></a>
    </nav>

    <a>
        <img src="uoa.jpeg" alt="University of Arkansas">
    </a>

    <h1>Mini Search Engine</h1>
    <!-- Search form -->
    <form method="post" action="">
        <label for="query">Enter your query:</label>
        <input type="text" id="query" name="query" required>
        <input type="submit" value="Submit Query">
    </form>

    <?php
        // Handle the form submission
        if ($_SERVER["REQUEST_METHOD"] == "POST") {
            $query = $_POST["query"];
            $command = "python3 query.py $query";
            $output = shell_exec($command);
            if (!empty($output)) {
                echo "<h3>Top 10 results:</h3>";
                echo '<ul id="resultList">';
                $results = explode("\n", $output);
                foreach ($results as $item) {
                    echo '<li title="Hover to view content" class="fileItem" data-filename="' . $item . '">';
                    echo '<a href="./files/' . $item . '">' . $item . '</a>';
                    echo '</li>';
                    
                }
                echo "</ul>";
            } else {
                echo "<p>No results found.</p>";
            }
        }
    ?>

    <!-- Content display box on the right -->
    <div id="contentDisplay"></div>

    <script>
        // Add event listeners for mouseover/mouseout events
        var resultList = document.getElementById('resultList');
        var contentDisplay = document.getElementById('contentDisplay');
        resultList.addEventListener('mouseover', handleMouseOver);
        resultList.addEventListener('mouseout', handleMouseOut);

        function handleMouseOver(event) {
                if (event.target.classList.contains('fileItem')) {
                    // If the mouse is over a file item, fetch and display content
                    var fileName = event.target.dataset.filename; // Extract the filename from data attribute
                    fetchContent(fileName);
                }
            }

        function handleMouseOut() {
            // Clear the content display when the mouse leaves
            clearContentDisplay();
        }

        function fetchContent(fileName) {
            // Fetch content using AJAX (replace with your actual endpoint or logic)
            var url = './files/' + fileName;
            fetch(url)
                .then(response => response.text())
                .then(content => displayContent(content))
                .catch(error => console.error('Error fetching content:', error));
        }

        function displayContent(content) {
            // Display content in the content display box
            contentDisplay.innerHTML = content;
            contentDisplay.style.display = 'block';
        }

        function clearContentDisplay() {
            // Clear the content display and hide the box
            contentDisplay.innerHTML = '';
            contentDisplay.style.display = 'none';
        }
    </script>

    <footer>
        Created & maintained by <strong>Quan Mai</strong>,
        with much help from <a rel="Website" href="https://chat.openai.com" target="_blank">ChatGPT</a>.
        Website content licensed <a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank">CC BY-NC-SA 4.0</a>.
        <!--<p>&copy; Created by Quan Mai, thanks to ChatGPT and Internet</p>-->
    </footer>
</body>

</html>
