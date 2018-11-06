var train_data = {
  name: "",
  telpon: "",
  alamat: "",
  file: null
};
var message = null;

var recognize_data = {
  imageBase64: null
};

setTimeout(function() {
  $(".alert").slideUp();
}, 3000);

function render() {
  //clear form data
  $(".form-item input").val("");
}

var monthControl = document.querySelector('input[type="month"]');
function cetak() {
  console.log(monthControl.value);
}

//  data table
// (function() {
//   $.ajax({
//     type: "GET",
//     url: "http://localhost:5000/karyawanData",
//     success: (data) => {
//       $('#example').DataTable({
//         data: JSON.parse(data),
//         columns: [
//           { title: "Id_user" },
//           { title: "Username" },
//           { title: "Telpon" },
//           { title: "Alamar" }
//       ]
//       });
//     console.log(data)
//     }
//   }).done(function(res) {
//     console.log("get data");
//   });
// })();
// end data table

// function setupData() {
//   $(document).ready(function() {

//     $('#example').DataTable({
//       "ajax": {
//         "url": "http://localhost:5000/karyawanData",
//         "dataType": "json",
//         "dataSrc": "data",
//         "contentType": "application/json"
//       },
//       "columns": "data"
//     });
//   });
// }
// $(window).on("load", setupData);

(function() {
  $.ajax({
    type: "GET",
    url: "http://localhost:5000/absenPulang",
    success: function(data) {
      var t = "";
      console.log(data);
      for (var i = 0; i < data.length; i++) {
        var tr = "<tr>";
        tr += "<td>" + data[i][2] + "</td>";
        tr += "<td>" + data[i][6] + "</td>";
        tr += "<td>" + data[i][7] + "</td>";
        tr += "<td>" + data[i][5] + "</td>";
        tr += "</tr>";
        t += tr;
      }
      document.getElementById("data").innerHTML = t;
    }
  }).done(function(res) {
    console.log("get absen today");
  });
})();

function update() {
  if (message) {
    //render message
    $("message").html(
      '<p class="' +
        _.get(message, "type") +
        '">' +
        _.get(message, "message") +
        "</p>"
    );
  }
}

// sidebar
$(document).ready(function() {
  $("#sidebarCollapse").on("click", function() {
    $("#sidebar").toggleClass("active");
  });
});

// // jam
// var myVar = setInterval(myTimer, 1000);
// function myTimer() {
//   var d = new Date();
//   var sqliteDate = d.toISOString();
//   document.getElementById("jam").innerHTML = d.toLocaleTimeString();
// }
window.onload = function onld() {
  function startTime() {
    var today = new Date();
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();
    m = checkTime(m);
    s = checkTime(s);
    document.getElementById("jam").innerHTML = h + ":" + m + ":" + s;
    var t = setTimeout(startTime, 500);
  }
  function checkTime(i) {
    if (i < 10) {
      i = "0" + i;
    } // add zero in front of numbers < 10
    return i;
  }

  startTime();
} 
  


$(document).ready(function() {
  //listen for file added
  $("#tambah #input-file").on("change", function(event) {
    // console.log("file is added with file is", event.target.files);

    // set file object to train data
    train_data.file = _.get(event, "target.files[0]", null);
  });

  //listen for name changed
  $("#name-field").on("change", function(event) {
    train_data.name = _.get(event, "target.value", "");
  });

  $("#telpon-field").on("change", function(event) {
    train_data.telpon = _.get(event, "target.value", "");
  });

  $("#alamat-field").on("change", function(event) {
    train_data.alamat = _.get(event, "target.value", "");
  });

  //listen the form train submit
  $("#tambah").submit(function(event) {
    message = null;
    if (
      train_data.name &&
      train_data.telpon &&
      train_data.alamat &&
      train_data.file
    ) {
      //do send data to backend api

      var train_form_data = new FormData();

      train_form_data.append("name", train_data.name);
      train_form_data.append("telpon", train_data.telpon);
      train_form_data.append("alamat", train_data.alamat);
      train_form_data.append("file", train_data.file);

      axios
        .post("/tambah_karyawan", train_form_data)
        .then(function(response) {
          message = {
            type: "success",
            message:
              "training has been done, user with id is:" +
              _.get(response, "data.id")
          };
          update();
        })
        .catch(function(error) {
          message = {
            type: "error",
            message: _.get(
              error,
              "response.data.error.message",
              "unknown error."
            )
          };

          update();
        });
    } else {
      message = { type: "error", message: "name and face image is required" };
    }
    update();
    event.preventDefault();
  });

  // listen for recognize file field change
  $("#canvas").on("change", function(e) {
    recognize_data.imageBase64 = _.get(e, "target.files[0]", null);
  });

  (function() {
    var btnMasuk = document.getElementById("c-masuk");
    var btnPulang = document.getElementById("c-pulang");
    var video = document.getElementById("video"),
      canvas = document.getElementById("canvas"),
      image = document.getElementById('snap'),
      take_again = document.getElementById('repeat'),      
      context = canvas.getContext("2d"),
      vendorUrl = window.URL || window.webkitURL;

    navigator.getMedia =
      navigator.getUserMedia ||
      navigator.webkitGetUserMedia ||
      navigator.mozGetUserMedia ||
      navigator.msGetUserMedia;
    navigator.getMedia(
      {
        video: true,
        audio: false
      },
      function(stream) {
        video.src = vendorUrl.createObjectURL(stream);
        video.play();
      },
      function(error) {
        //error handled
      }
    );

    // button absensi masuk
    btnMasuk.addEventListener("click", function() {
      console.log("absen masuk jalan");
      // context.drawImage(video, 0, 0, 400, 300);
      // var dataURL = canvas.toDataURL();

      var snap = takeSnapshot();

      // Show image. 
      image.setAttribute('src', snap);
      image.classList.add("visible");

      // Enable delete and save buttons
      take_again.classList.remove("disabled");

      // Pause video playback of stream.
      video.pause();

      // kirim data ke url /absen masuk
      $.ajax({
        type: "POST",
        url: "http://localhost:5000/absenMasuk",
        data: {
          imageBase64: snap
        },
        success: function(data) {
          if (typeof data == "object") {
            var t = "";
            for (var i = 0; i < data.length; i++) {
              var tr = "<tr>";
              tr += "<td>" + data[i][2] + "</td>";
              tr += "<td>" + data[i][6] + "</td>";
              tr += "<td>" + data[i][7] + "</td>";
              tr += "<td>" + data[i][5] + "</td>";
              tr += "</tr>";
              t += tr;
            }
            document.getElementById("data").innerHTML = t;
          } else {
            alert(data);
          }
        },
        error: function(err) {
          alert(err.responseJSON.error.message);
        }
      }).done(function(res) {
        console.log("absen selesai");
      });
    });

    take_again.addEventListener("click", function(e){

      e.preventDefault();
    
      // Hide image.
      image.setAttribute('src', "");
      image.classList.remove("visible");
    
      // Disable delete and save buttons
      take_again.classList.add("disabled");
    
      // Resume playback of stream.
      video.play();
    
    });
    
    // button absensi Pulang
    btnPulang.addEventListener("click", function() {
      console.log("absen pulang jalan");
      // context.drawImage(video, 0, 0, 400, 300);
      // var dataURL = canvas.toDataURL();

      var snap = takeSnapshot();
      
      // Show image. 
      image.setAttribute('src', snap);
      image.classList.add("visible");

      // Enable delete and save buttons
      take_again.classList.remove("disabled");

      // Pause video playback of stream.
      video.pause();

      // kirim data ke url /absenPulang
      $.ajax({
        type: "POST",
        url: "http://localhost:5000/absenPulang",
        data: {
          imageBase64: snap
        },
        success: function(data) {
          var t = "";
          for (var i = 0; i < data.length; i++) {
            var tr = "<tr>";
            tr += "<td>" + data[i][2] + "</td>";
            tr += "<td>" + data[i][6] + "</td>";
            tr += "<td>" + data[i][7] + "</td>";
            tr += "<td>" + data[i][5] + "</td>";
            tr += "</tr>";
            t += tr;
          }
          document.getElementById("data").innerHTML = t;
        },
        error: function(err) {
          alert(err.responseJSON.error.message);
        }
      }).done(function(res) {
        console.log("saved");
        // If you want the file to be visible in the browser
        // - please modify the callback in javascript. All you
        // need is to return the url to the file, you just saved
        // and than put the image in your browser.
      });
    });

    function takeSnapshot(){
      // Here we're using a trick that involves a hidden canvas element.  
    
      // var hidden_canvas = document.getElementById('canvas'),
      //     context = hidden_canvas.getContext('2d');
    
      var width = video.videoWidth,
          height = video.videoHeight;
    
      if (width && height) {
    
        // Setup a canvas with the same dimensions as the video.
        canvas.width = width;
        canvas.height = height;
    
        // Make a copy of the current frame in the video on the canvas.
        context.drawImage(video, 0, 0, width, height);
    
        // Turn the canvas image into a dataURL that can be used as a src for our photo.
        return canvas.toDataURL();
      }
    }
  })();

  // $("#recognize").submit(function(e) {
  //   console.log("recognize is submitted", recognize_data);

  //   // call to backend
  //   var recog_form_data = new FormData();
  //   recog_form_data.append("canvas", recognize_data.imageBase64);

  //   axios
  //     .post("/absenMasuk", recog_form_data)
  //     .then(function(response) {
  //       console.log(
  //         "We found a user matched with your face image is",
  //         response.data
  //       );

  //       message = {
  //         type: "success",
  //         message:
  //           "We found a user matched with your face image is: " +
  //           response.data.user.name
  //       };

  //       recognize_data = { imageBase64: null };
  //       update();
  //     })
  //     .catch(function(err) {
  //       message = {
  //         type: "error",
  //         message: _.get(err, "response.data.error.message", "Unknown error")
  //       };

  //       update();
  //     });
  //   e.preventDefault();
  // });

  render();
});
