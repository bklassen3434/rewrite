import { wrapTextNodesInBlockElements, delay, normalizeText } from "/src/utils/index.js";

// globl vars
var baseURL = "http://localhost:3001"; // local development
var stats = {
  simplify: 0,
  exemplify: 0,
  factcheck: 0,
  assert: 0,
  clarify: 0,
};

// start ReWrite once page loads
window.addEventListener("load", function () {
  init();
});

/**
 * Start ReWrite app.
 */
function init() {
  // setInterval(() => {
  //   const responseBox = document.getElementById("response-input");
  //   const responseBoxText = responseBox ? responseBox.innerText : "";

  //   fetch("/track-edits", {
  //     method: "POST",
  //     headers: {
  //       "Content-Type": "application/json",
  //     },
  //     body: JSON.stringify({ responseBoxText }),
  //   })
  //     .then((response) => response.json())
  //     .then((data) => {
  //       // console.log('Edit tracking response:', data);
  //     })
  //     .catch((error) => {
  //       console.error("Error tracking edits:", error);
  //     });
  // }, 3000); // Runs every 3 seconds

  // // Store the evolving data points for each metric
  // let metricsData = {
  //   Clarify: [0],
  //   Assert: [0],
  //   FactCheck: [0],
  //   Exemplify: [0],
  //   Simplify: [0],
  // };

  // let editCount = 0; // Tracks the number of edits (time)

  // // Set up a MutationObserver to detect changes in the table cells
  // const tableObserver = new MutationObserver((mutationsList) => {
  //   for (let mutation of mutationsList) {
  //     if (mutation.type === "characterData" || mutation.type === "childList") {
  //       updateChartData();
  //       break; // Update once per batch of mutations
  //     }
  //   }
  // });

  // // Observe changes in the specific table cells
  // ["clarify", "assert", "fact-check", "exemplify", "simplify"].forEach((id) => {
  //   const targetNode = document.getElementById(id);
  //   tableObserver.observe(targetNode, { characterData: true, childList: true, subtree: true });
  // });

  // // Initial chart draw
  // drawChart();

  // setup and start event handling for track changes
  // See: <https://github.com/nytimes/ice>
  const responseInput = document.getElementById("response-input");
  window.tracker = new ice.InlineChangeEditor({
    element: responseInput,
    handleEvents: true,
    currentUser: { id: 11, name: "Geoffrey Jellineck" },
    plugins: [
      "IceAddTitlePlugin",
      "IceSmartQuotesPlugin",
      "IceEmdashPlugin",
      {
        name: "IceCopyPastePlugin",
        settings: {
          pasteType: "formattedClean",
          preserve: "p,a[href],i,em,b,span,ul,ol,li,hr",
        },
      },
    ],
  }).startTracking();

  // clear tables
  fetch(`${baseURL}/clear-tables`, { method: "GET" });

  // Add event listeners
  document.getElementById("highlight-toggle").addEventListener("click", onToggleUserEditsClick);
  document.getElementById("sub-but").addEventListener("click", onSubmitButtonClick);
  document.getElementById("refresh-but").addEventListener("click", onRefreshButtonClick);
}

/**
 * Toggles the visibility of user edits.
 */
function onToggleUserEditsClick() {
  const responseInput = document.getElementById("response-input");
  const highlightToggleButton = $(this);
  if ($(responseInput).hasClass("CT-hide")) {
    $(responseInput).removeClass("CT-hide");
    $(highlightToggleButton).removeClass("CT-hide");
    $(highlightToggleButton).children(".text").text("Hide your edits!");
  } else {
    $(responseInput).addClass("CT-hide");
    $(highlightToggleButton).addClass("CT-hide");
    $(highlightToggleButton).children(".text").text("Show your edits!");
  }
}

/**
 * TODO
 */
function onSubmitButtonClick() {
  // Retrieve input values (source text and essay prompt)
  const sourceText = document.getElementById("source-input").value;
  const essayPrompt = document.getElementById("essay-input").value;
  const submitButton = document.getElementById("sub-but");

  // Validation check
  if (!sourceText || !essayPrompt) {
    console.log("Error: sourceText or essayPrompt are empty.");
    alert("Please fill out both the source text and the essay prompt.");
    return;
  }

  // Loading feedback to user (locks evaluate button to prevent multiple submissions)
  submitButton.innerText = "Loading...";
  submitButton.disabled = true;
  // document.getElementById('response-input').innerText = "Loading...";
  const responseInput = document.getElementById("response-input");

  // responseInput.innerText = "Loading...";
  responseInput.innerHTML = "<p>Loading...</p>";

  // Request contains the source text and essay prompt
  const url = `${baseURL}/generate`;
  const request = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source_text: sourceText,
      essay_prompt: essayPrompt,
    }),
  };

  // Send a POST request to http://localhost:3001/generate
  fetch(url, request)
    .then((response) => response.json())
    .then((data) => {
      // Handle server response
      // Parses JSON response, updates response box, and saves the response

      // document.getElementById('response-input').innerText = data.response;
      // responseInput.innerText = data.response || "<p>Default response content</p>";

      responseInput.innerHTML = data.response || "<p>Default response content</p>";

      wrapTextNodesInBlockElements(responseInput);

      if (!responseInput.firstChild) {
        console.warn("responseInput is empty. Adding a default <p> node.");
        responseInput.innerHTML = "<p>Default response content</p>";
      }

      // Reset submit button
      submitButton.innerText = "STEP 3: Submit to ReWrite";
      submitButton.disabled = false;
    })
    .catch((error) => {
      // Error handling
      console.error("Error:", error);
      submitButton.innerText = "STEP 3: Submit to ReWrite";
      submitButton.disabled = false;
    });
}

/**
 * Utility function for fetch operations
 */
async function fetchEdits(essay, sourceText) {
  try {
    // Request contains the essay and source text
    const url = `${baseURL}/evaluate`;
    const request = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ essay, sourceText }),
    };

    // Send a POST request to http://localhost:3001/evaluate
    const response = await fetch(url, request);
    const data = await response.json();

    // `data` is a list of [{ type: "string", edits: [...] }, ...]
    // console.log(data);

    // parse each type of edit
    data.forEach(({ type, edits }) => {
      // stats[type] = data[`${type}_number`];
      (edits[`context`] || []).forEach((phrase, index) => {
        // const startIndex = essay.indexOf(phrase);
        // const endIndex = startIndex + phrase.length;

        // Normalize both the essay and the phrase
        const normalizedEssay = normalizeText(essay);
        const normalizedPhrase = normalizeText(phrase);

        // Find the index of the normalized phrase in the normalized essay
        const startIndex = normalizedEssay.indexOf(normalizedPhrase);
        const endIndex = startIndex + normalizedPhrase.length;

        if (startIndex === -1) {
          console.warn(`Phrase "${phrase}" not found in text.`);
          return;
        }
        // const phraseRegex = new RegExp(`\\b${phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
        const suggestion = edits[`suggestion`][index] || `No suggestion for this ${type} edit.`;
        const reasoning = edits[`reasoning`][index] || `No reasoning for this ${type} edit.`;
        // const highlightId = addEditToTable(evaluateClickCount, type.charAt(0).toUpperCase() + type.slice(1), phrase, suggestion, false);
        const edit = {
          type,
          phrase,
          suggestion,
          reasoning,
          startIndex,
          endIndex,
          completed: false,
        };

        // highlightedText = highlightedText.replace(
        //     phraseRegex,
        //     `<span class="${type}_highlight highlight-span" data-type="${type}" data-highlight-id="${highlightId}" data-suggestion="${suggestion}" data-reasoning="${reasoning}" data-start-index="${startIndex}" data-end-index="${endIndex}">${phrase}<span class="tooltip-content"><span class="tooltip-check"><input type="checkbox" class="edit-check" data-completed="false" onchange="toggleCompletion(this)"><label>Mark as Completed</label></span></span></span>`
        // );

        // Push edit to the backend database
        storeEditInBackend(edit);
      });
    });
  } catch (error) {
    console.error(`Error during ${type} fetch:`, error);
  }
}

/**
 * TODO
 * @param {*} edit
 */
async function storeEditInBackend(edit) {
  try {
    const url = `${baseURL}/store-edits`;
    const request = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edits: [edit] }),
    };
    const response = await fetch(url, request);
    const data = await response.json();
    // console.log("Edit successfully stored:", data);
  } catch (error) {
    console.error("Error storing edit in backend:", error);
  }
}

/**
 * TODO
 * @returns
 */
async function fetchStoredEdits() {
  try {
    const url = `${baseURL}/get-edits`;
    const request = { method: "GET" };
    const response = await fetch(url, request);
    const data = await response.json();
    console.log(data.edits);
    return data.edits;
  } catch (error) {
    console.error("Error fetching stored edits:", error);
    return [];
  }
}

/**
 * TODO
 * @param {*} storedEdits
 */
async function updateTable(storedEdits) {
  const categoryCounts = storedEdits.reduce((counts, edit) => {
    counts[edit.type] = (counts[edit.type] || 0) + 1;
    return counts;
  }, {});

  console.log(categoryCounts);

  // Populate table dynamically
  Object.keys(stats).forEach((type) => {
    try {
      document.getElementById(`${type}`).innerText = categoryCounts[type] || 0;
    } catch (error) {
      console.error(`Error processing type "${type}":`, error);
      // Optionally, you can handle specific cases here, e.g., setting default values.
    }
  });
}

/**
 * TODO
 */
async function onRefreshButtonClick() {
  const sourceText = document.getElementById("source-input").value;
  const responseBox = document.getElementById("response-input");
  const refreshButton = document.getElementById("refresh-but");

  // Validation check
  if (!responseBox.innerText.trim() || responseBox.innerText.trim() === "ReWrite's Response") {
    console.log("Error: No essay to evaluate.");
    alert("Please generate a response first.");
    return;
  }

  // Validation check
  if (!sourceText) {
    console.log("Error: sourceText is empty.");
    alert("Please fill out both the source text and the essay prompt.");
    return;
  }

  const essay = responseBox.innerText;

  refreshButton.innerText = "Loading...";
  refreshButton.disabled = true;

  let highlightedText = essay;

  try {
    // request edits from backend
    await fetchEdits(essay, sourceText);

    // Fetch all stored edits and apply highlights
    const storedEdits = await fetchStoredEdits();

    // storedEdits.forEach((edit) => {
    //     const phraseRegex = new RegExp(`\\b${edit.phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
    //     highlightedText = highlightedText.replace(
    //         phraseRegex,
    //         `<span class="${edit.type}_highlight highlight-span" data-type="${edit.type}" data-suggestion="${edit.suggestion}" data-reasoning="${edit.reasoning}" data-start-index="${edit.startIndex}" data-end-index="${edit.endIndex}">${edit.phrase}<span class="tooltip-content"><span class="tooltip-check"><input type="checkbox" class="edit-check" data-completed="${edit.completed}" onchange="toggleCompletion(this)"><label>Mark as Completed</label></span></span></span>`
    //     );
    // });
    storedEdits.forEach((edit) => {
      const phraseRegex = new RegExp(`\\b${edit.phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "gi");

      highlightedText = highlightedText.replace(phraseRegex, (match) => {
        // Check if the match is already highlighted
        const existingMatch = match.match(/<span[^>]*class="([^"]*)"/);
        const existingTypes = match.match(/data-type="([^"]*)"/);

        let types = existingTypes ? existingTypes[1].split(",") : [];
        let newClass = `${edit.type}_highlight highlight-span`;

        // Add the new type if not already present
        if (!types.includes(edit.type)) {
          types.push(edit.type);
        }

        // Generate box-shadow styles dynamically
        const shadowColors = {
          clarify: "lightcoral",
          assert: "lightgreen",
          factcheck: "lightblue",
          exemplify: "pink",
          simplify: "lightsalmon",
        };

        const boxShadows = types.map((type) => `0 0 0 2px ${shadowColors[type]}`).join(",");

        // Combine classes if already highlighted
        if (existingMatch) {
          const existingClasses = existingMatch[1];
          if (!existingClasses.includes(edit.type)) {
            newClass = `${existingClasses} ${edit.type}_highlight`;
          }
        }

        return `<span class="${newClass}" data-type="${types.join(",")}" data-suggestion="${
          edit.suggestion
        }" data-reasoning="${edit.reasoning}" style="--highlight-shadows: ${boxShadows}">${match}</span>`;
      });
    });

    responseBox.innerHTML = highlightedText.replace(/\n/g, "<br>");
    await updateTable(storedEdits);
  } catch (error) {
    console.error("Error:", error);
  } finally {
    refreshButton.innerText = "STEP 5: Evaluate Essay";
    refreshButton.disabled = false;
  }
}

// /**
//  * TODO
//  * @returns
//  */
// function collectEdits() {
//   const edits = [];
//   document.querySelectorAll(".highlight-span").forEach((highlight) => {
//     const type = highlight.dataset.type; // e.g., Simplify, Exemplify
//     const phrase = highlight.innerText; // Highlighted text
//     const suggestion = highlight.dataset.suggestion; // Suggestion text
//     const reasoning = highlight.dataset.reasoning; // Suggestion text
//     const highlightId = highlight.dataset.highlightId; // Highlight ID
//     const startIndex = parseInt(highlight.dataset.startIndex, 10); // Start index
//     const endIndex = parseInt(highlight.dataset.endIndex, 10); // End index
//     const completed = highlight.querySelector(".edit-check").checked; // Completion status

//     edits.push({
//       type,
//       phrase,
//       suggestion,
//       reasoning,
//       highlightId,
//       startIndex,
//       endIndex,
//       completed,
//     });
//   });
//   return edits;
// }

// /**
//  * TODO
//  * @param {*} edits
//  */
// async function sendEditsToBackend(edits) {
//   try {
//     const url = `${baseURL}/store-edits`;
//     const request = {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify({ edits }),
//     };
//     const response = await fetch(url, request);
//     const data = await response.json();
//     console.log("Edits successfully sent:", data);
//   } catch (error) {
//     console.error("Error sending edits to backend:", error);
//   }
// }

// /**
//  * Function to update the chart data
//  */
// function updateChartData() {
//   editCount++;

//   // Get the latest values from the table
//   metricsData.Clarify.push(parseInt(document.getElementById("clarify").textContent));
//   metricsData.Assert.push(parseInt(document.getElementById("assert").textContent));
//   metricsData.FactCheck.push(parseInt(document.getElementById("fact-check").textContent));
//   metricsData.Exemplify.push(parseInt(document.getElementById("exemplify").textContent));
//   metricsData.Simplify.push(parseInt(document.getElementById("simplify").textContent));

//   drawChart();
// }

// /**
//  * TODO
//  */
// function drawChart() {
//   // Clear existing SVG content before re-rendering
//   d3.select("#bar-chart").selectAll("*").remove();

//   var chartHeight = document.querySelector(".chart-container").clientHeight;
//   var margin = { top: 20, right: 20, bottom: 30, left: 60 };
//   var width = document.getElementById("bar-chart").clientWidth - margin.left - margin.right;
//   var height = chartHeight - margin.top - margin.bottom;

//   // Create an SVG container
//   var svg = d3
//     .select("#bar-chart")
//     .append("svg")
//     .attr("width", width + margin.left + margin.right)
//     .attr("height", height + margin.top + margin.bottom)
//     .append("g")
//     .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

//   // X scale: Time (number of edits)
//   var xScale = d3
//     .scaleLinear()
//     .domain([0, editCount]) // Number of edits so far
//     .range([0, width]);

//   // Y scale: Metric values
//   var yScale = d3
//     .scaleLinear()
//     .domain([0, d3.max(Object.values(metricsData).flat())]) // Max value from all metrics
//     .range([height, 0]);

//   // Append the Y axis
//   svg.append("g").call(d3.axisLeft(yScale).ticks(5));

//   // Define custom colors for each metric
//   const colorMap = {
//     Clarify: "#F08080",
//     Assert: "#90EE90",
//     FactCheck: "#ADD8E6",
//     Exemplify: "#FFC0CB",
//     Simplify: "#FFA07A",
//   };

//   // Draw lines and circles for each metric
//   Object.keys(metricsData).forEach((key) => {
//     svg
//       .append("path")
//       .datum(metricsData[key])
//       .attr("fill", "none")
//       .attr("stroke", colorMap[key]) // Use custom color
//       .attr("stroke-width", 3) // Increased line width
//       .attr(
//         "d",
//         d3
//           .line()
//           .x((d, index) => xScale(index)) // Index is the edit time
//           .y((d) => yScale(d)) // Metric value
//       );

//     // Add circles at each data point
//     svg
//       .selectAll(".circle-" + key)
//       .data(metricsData[key])
//       .enter()
//       .append("circle")
//       .attr("cx", (d, index) => xScale(index))
//       .attr("cy", (d) => yScale(d))
//       .attr("r", 4) // Circle radius
//       .attr("fill", colorMap[key]); // Use custom color
//   });

//   // Add title
//   svg
//     .append("text")
//     .attr("x", width / 2)
//     .attr("y", -5)
//     .attr("text-anchor", "middle")
//     .attr("font-size", "16px")
//     .attr("font-weight", "bold")
//     .attr("font-family", "'Anton', sans-serif")
//     .text("Flag Tracker");
// }
