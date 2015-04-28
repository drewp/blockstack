www/README.html: README.md
	markdown README.md > www/README.html

install_modules:
	sudo aptitude install liblinearmath2.82 libbulletcollision2.82 libbulletdynamics2.82 libbulletsoftbody2.82 libode1

