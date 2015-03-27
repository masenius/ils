<html>
<head>
<title>iLoveSkydiving - A fan page</title>
<link rel="stylesheet" type="text/css" href="style.css">
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-18326596-2', 'auto');
  ga('send', 'pageview');
</script>
</head>
<body>
<div id="videos">
  <input class="search" placeholder="Filter" />
  <button class="sort" data-sort="date">
    Sort by date
  </button>
  <button class="sort" data-sort="shares">
    Sort by shares
  </button>
  <a class="button" target="_blank" href="http://iloveskydiving.org/">
    Go to iLoveSkydiving
  </a>
  &replace&
 </div>
 <script src="http://listjs.com/no-cdn/list.js"></script>
 <script>
	var options = {
		valueNames: [ 'date', 'shares', 'title', 'tags' ],
    page: 3000,
	};

	var videosList = new List('videos', options);
</script>
</body>
</html>
