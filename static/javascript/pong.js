import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

class App {
	constructor() {
		const divContainer = document.querySelector("#webgl-container");
		this._divContainer = divContainer;

		const renderer = new THREE.WebGLRenderer({antialias: true});
		renderer.setPixelRatio(window.devicePixelRatio);
		divContainer.appendChild(renderer.domElement);
		// renderer.domElement -> canvas타입의 dom객체
		this._renderer = renderer;

		const scene = new THREE.Scene();
		scene.background = new THREE.Color(0x87ceeb);
		this._scene = scene;

		this._p1score = 0;
		this._p2score = 0;

		const div_p1score = document.getElementById("p1-score");
		const div_p2score = document.getElementById("p2-score");

		this._div_p1score = div_p1score;
		this._div_p2score = div_p2score;

		this._setupCamera();
		this._setupLight();
		this._setupModel();
		this._setupControls();
		this._setupKeyboardControls();

		window.onresize = this.resize.bind(this);
		//window.onresize -> 창크기 변경시 발생하는 메서드
		this.resize(); //renderer와 camera의 속성을 창크기에 맞게 설정해주기 위함.

		requestAnimationFrame(this.render.bind(this));
	}

	_sleep(sec) {
		let start = Date.now(), now = start;
		while (now - start < sec * 1000) {
			now = Date.now();
		}
	}

	_setupKeyboardControls() {
		const keyboardState = {};
		this._keyboardState = keyboardState;

		document.addEventListener('keydown', (event) => {
			this._keyboardState[event.code] = true;
		});
		document.addEventListener('keyup', (event) => {
			this._keyboardState[event.code] = false;
		});
	}

	_setupControls() {
		new OrbitControls(this._camera, this._divContainer);
	}


	_setupCamera() {
		const width = this._divContainer.clientWidth;
		const height = this._divContainer.clientHeight;
		// const camera = new THREE.OrthographicCamera(
		// 	-5,
		// 	5,
		// 	2,
		// 	-2,
		// 	0.1,
		// 	100
		// );
		const camera = new THREE.PerspectiveCamera(
			75,
			width / height,
			0.1,
			100
		);
		const cam_pos = new THREE.Vector3(0, 0, 3);
		camera.position.copy(cam_pos);
		camera.lookAt(0, 0, 0);
		this._camera = camera;
	}

	_setupLight() {
		const light = new THREE.AmbientLight(0xffffff, 0.2);

		this._scene.add(light);
		this._light = light;

		const color = 0xffffff; // 광원의 색상.
		const intensity = 1; //광원의 세기.
		const direct_light = new THREE.DirectionalLight(color, intensity);
		direct_light.position.set(-1, 2, 4);
		this._scene.add(direct_light);
		this._direct_light = direct_light;
	}

	_setupGround() {
		const UpperPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 1.5);
		const LowerPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 1.5);
		const RightSidePlane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 3);
		const LeftSidePlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), 3);

		this._UpperPlane = UpperPlane;
		this._LowerPlane = LowerPlane;
		this._RightSidePlane = RightSidePlane;
		this._LeftSidePlane = LeftSidePlane;

		const UpperPlaneHelper = new THREE.PlaneHelper( UpperPlane, 6, 0xff0000 );
		this._scene.add( UpperPlaneHelper );
		const LowerPlaneHelper = new THREE.PlaneHelper( LowerPlane, 6, 0xffff00 );
		this._scene.add( LowerPlaneHelper );
		const RightSidePlaneHelper = new THREE.PlaneHelper( RightSidePlane, 3, 0x0000ff );
		this._scene.add( RightSidePlaneHelper );
		const LeftSidePlaneHelper = new THREE.PlaneHelper( LeftSidePlane, 3, 0xffffff );
		this._scene.add( LeftSidePlaneHelper );
	}

	_setupModel() {
		this._setupGround();

		const Boxgeometry = new THREE.BoxGeometry(0.08, 0.7, 0.1); // 인자 : 가로, 세로, 깊이
		const Boxmaterial_1 = new THREE.MeshStandardMaterial({
			color: 0xff0000});
		const Boxmaterial_2 = new THREE.MeshStandardMaterial({
				color: 0x00ff00});

		const cube_1 = new THREE.Mesh(Boxgeometry, Boxmaterial_1);
		cube_1.position.x = 2.5;

		const cube_2 = new THREE.Mesh(Boxgeometry, Boxmaterial_2);
		cube_2.position.x = -2.5;

		cube_1.geometry.computeBoundingBox();
		cube_2.geometry.computeBoundingBox(); //static geometry일 경우 한번만 계산.

		const BBcube_1 = new THREE.Box3();
		const BBcube_2 = new THREE.Box3();

		this._BBcube_1 = BBcube_1;
		this._BBcube_2 = BBcube_2;

		this._scene.add(cube_2);
		this._scene.add(cube_1);
		this._cube_1 = cube_1;
		this._cube_2 = cube_2;

		const Spheregeometry = new THREE.SphereGeometry(0.04, 32, 32);
		const Spherematerial = new THREE.MeshStandardMaterial({
			color: 0xffffff});

		const sphere = new THREE.Mesh(Spheregeometry, Spherematerial);
		this._scene.add(sphere);
		this._sphere = sphere;

		this._sphere_speed = 0.03;
		this._sphere_direction = new THREE.Vector3(1, 1, 0).normalize();

		const _BBsphere = new THREE.Sphere(sphere.position, 0.04);
		this._BBsphere = _BBsphere;
	}

	resize() { 
		const width = this._divContainer.clientWidth;
		const height = this._divContainer.clientHeight;

		this._camera.aspect = width / height;
		this._camera.updateProjectionMatrix();

		this._renderer.setSize(width, height);
	}

	render(time) {
		// exit game
		if (this._p1score == 10 || this._p2score == 10)
			return;
		this._renderer.render(this._scene, this._camera);
		this.update(time);
		requestAnimationFrame(this.render.bind(this));
	}

	_CheckKeyboardInput() {
		//cube_1 (red cube moving)
		if (this._keyboardState['ArrowUp']) {
			if (!this._BBcube_1.intersectsPlane(this._UpperPlane)) {
				this._cube_1.position.y += 0.05;
			}
		}
		if (this._keyboardState['ArrowDown']) {
			if (!this._BBcube_1.intersectsPlane(this._LowerPlane)) {
				this._cube_1.position.y -= 0.05;
			}
		}

		// cube_2 (green cube moving)
		if (this._keyboardState['KeyW']) {
			if (!this._BBcube_2.intersectsPlane(this._UpperPlane)) {
				this._cube_2.position.y += 0.05;
			}
		}
		if (this._keyboardState['KeyS']) {
			if (!this._BBcube_2.intersectsPlane(this._LowerPlane)) {
				this._cube_2.position.y -= 0.05;
			}
		}
	}

	_CheckBallCollision() {
		if (this._BBsphere.intersectsPlane(this._UpperPlane)) {
			this._BallHitPlane(this._UpperPlane);
		}
		if (this._BBsphere.intersectsPlane(this._LowerPlane)) {
			this._BallHitPlane(this._LowerPlane);
		}
		if (this._BBsphere.intersectsPlane(this._RightSidePlane)) {
			this._sphere.position.set(0, 0, 0);
			this._p1score += 1;
			this._sleep(1.5);
		}
		if (this._BBsphere.intersectsPlane(this._LeftSidePlane)) {
			this._sphere.position.set(0, 0, 0);
			this._p2score += 1;
			this._sleep(1.5);
		}
		if (this._BBsphere.intersectsBox(this._BBcube_1)) {
			this._BallHitBox(new THREE.Vector3(-1, 0, 0), this._cube_1.position);
		}
		if (this._BBsphere.intersectsBox(this._BBcube_2)) {
			this._BallHitBox(new THREE.Vector3(1, 0, 0), this._cube_2.position);
		}
	}

	_BallHitPlane( plane ) {
		let dot_product = this._sphere_direction.dot(plane.normal.normalize());
		if (dot_product < 0) dot_product = dot_product * -1;
		const tmp_vector = new THREE.Vector3();
		tmp_vector.copy(this._sphere_direction);
		tmp_vector.addScaledVector(plane.normal.normalize(), dot_product).multiplyScalar(2);
		tmp_vector.sub(this._sphere_direction).normalize();
		this._sphere_direction.copy(tmp_vector);
	}

	_BallHitBox( normal, position ) {
		const tmp_vector = new THREE.Vector3();
		tmp_vector.subVectors(this._sphere.position, position).add(normal);
		this._sphere_direction.copy(tmp_vector).normalize();
	}

	update( time ) {
		this._CheckKeyboardInput();

		this._BBcube_1.copy(this._cube_1.geometry.boundingBox).applyMatrix4(this._cube_1.matrixWorld);
		this._BBcube_2.copy(this._cube_2.geometry.boundingBox).applyMatrix4(this._cube_2.matrixWorld);
		// this._BBsphere.applyMatrix4(this._sphere.matrixWorld);

		this._sphere.position.addScaledVector(this._sphere_direction, this._sphere_speed);

		this._CheckBallCollision();
		this._div_p1score.innerHTML = "P1 Score : " + this._p1score;
		this._div_p2score.innerHTML = "P2 Score : " + this._p2score;
	}
}

window.onload = function() {
	new App();
}