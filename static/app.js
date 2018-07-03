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

function render() {
  //clear form data
  $(".form-item input").val("");
}


(function() {
  $.ajax({
    type: "GET",
    url: "http://localhost:5000/absenPulang",
    success: function(data) {
      for (var i = 0; i < data.length; i++) {
        $("#preview-absen #n").html(data[i][2]);
        $("#preview-absen #sm").html(data[i][6]);
        if(data[i][7] == null) {
          $("#preview-absen #sp").html("None");
        } else {
          $("#preview-absen #sp").html(data[i][7]);
        }
        if(data[i][5] == null) {
          $("#preview-absen #ket").html("None");
        } else {
          $("#preview-absen #ket").html(data[i][5]);
        }
      }
    }
  }).done(function(res) {
    console.log("get absen today");
  });
})()

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

// datatables
// $('#mydata').dataTable();

// jam
var myVar = setInterval(myTimer, 1000);

function myTimer() {
  var d = new Date();
  var sqliteDate = d.toISOString();
  document.getElementById("jam").innerHTML = d.toLocaleTimeString();
}

function takephoto() {
  var d = new Date();
  console.log(d.toLocaleTimeString());
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
      context = canvas.getContext("2d"),
      photo = document.getElementById("photo"),
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
      context.drawImage(video, 0, 0, 400, 300);
      var dataURL = canvas.toDataURL();

      // kirim data ke url /absen masuk
      $.ajax({
        type: "POST",
        url: "http://localhost:5000/absenMasuk",
        data: {
          imageBase64: dataURL
        },
        success: function(data) {
          if (typeof(data) == "object"){
            for (var i = 0; i < data.length; i++) {
              $("#preview-absen #n").html(data[i][2]);
              $("#preview-absen #sm").html(data[i][6]);
              if(data[i][7] == null) {
                $("#preview-absen #sp").html("None");
              } else {
                $("#preview-absen #sp").html(data[i][7]);
              }
              if(data[i][5] == null) {
                $("#preview-absen #ket").html("None");
              } else {
                $("#preview-absen #ket").html(data[i][5]);
              }
            }
          } else{
            alert(data)
          }
        },
        error: function(err) {
          alert(err.responseJSON.error.message)
        }
      }).done(function(res) {
        console.log("absen selesai");
      });
    });

    // button absensi Pulang
    btnPulang.addEventListener("click", function() {
      console.log("absen pulang jalan");
      context.drawImage(video, 0, 0, 400, 300);
      var dataURL = canvas.toDataURL();

      // kirim data ke url /absenPulang
      $.ajax({
        type: "POST",
        url: "http://localhost:5000/absenPulang",
        data: {
          imageBase64: dataURL
        },
        success: function(data) {
          if (typeof(data) == "object"){
            for (var i = 0; i < data.length; i++) {
              $("#preview-absen #n").html(data[i][2]);
              $("#preview-absen #sm").html(data[i][6]);
              if(data[i][7] == null) {
                $("#preview-absen #sp").html("None");
              } else {
                $("#preview-absen #sp").html(data[i][7]);
              }
              if(data[i][5] == null) {
                $("#preview-absen #ket").html("None");
              } else {
                $("#preview-absen #ket").html(data[i][5]);
              }
            }
          } else{
            alert(data)
          }
        },
        error: function(err) {
          alert(err.responseJSON.error.message)
        }
      }).done(function(res) {
        console.log("saved");
        // If you want the file to be visible in the browser
        // - please modify the callback in javascript. All you
        // need is to return the url to the file, you just saved
        // and than put the image in your browser.
      });
      // photo.setAttribute('src', canvas.toDataURL('image/png'));
    });
  })();



  $("#recognize").submit(function(e) {
    console.log("recognize is submitted", recognize_data);

    // call to backend
    var recog_form_data = new FormData();
    recog_form_data.append("canvas", recognize_data.imageBase64);

    axios
      .post("/absenMasuk", recog_form_data)
      .then(function(response) {
        console.log(
          "We found a user matched with your face image is",
          response.data
        );

        message = {
          type: "success",
          message:
            "We found a user matched with your face image is: " +
            response.data.user.name
        };

        recognize_data = { imageBase64: null };
        update();
      })
      .catch(function(err) {
        message = {
          type: "error",
          message: _.get(err, "response.data.error.message", "Unknown error")
        };

        update();
      });
    e.preventDefault();
  });

  render();
});
