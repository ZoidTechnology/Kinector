#include <Kinect.h>
#include <Eigen/Dense>
#include <pybind11/pybind11.h>
#include "filter.h"

typedef struct {
	bool tracked;
	TIMESPAN previous;
	Joint joints[JointType_Count];
	Filter *filters[JointType_Count];
} Body;

IKinectSensor *sensor;
IBodyFrameReader *bodyFrameReader;
Body bodies[BODY_COUNT];

template<class Interface>
void Release(Interface *&toRelease) {
	if (toRelease) {
		toRelease->Release();
		toRelease = NULL;
	}
}

HRESULT Open() {
	if (sensor) {
		return E_FAIL;
	}

	HRESULT result = GetDefaultKinectSensor(&sensor);

	if (SUCCEEDED(result)) {
		result = sensor->Open();
	}

	IBodyFrameSource *bodyFrameSource = NULL;

	if (SUCCEEDED(result)) {
		result = sensor->get_BodyFrameSource(&bodyFrameSource);
	}

	if (SUCCEEDED(result)) {
		result = bodyFrameSource->OpenReader(&bodyFrameReader);
	}

	Release(bodyFrameSource);

	return result;
}

HRESULT Update(const float processNoise, const float observationNoise) {
	if (!sensor) {
		return E_FAIL;
	}

	IBodyFrame* bodyFrame = NULL;
	HRESULT result = bodyFrameReader->AcquireLatestFrame(&bodyFrame);
	TIMESPAN current;

	if (SUCCEEDED(result)) {
		result = bodyFrame->get_RelativeTime(&current);
	}

	Vector4 floorPlane;

	if (SUCCEEDED(result)) {
		result = bodyFrame->get_FloorClipPlane(&floorPlane);
	}

	Eigen::Matrix3f rotation;
	IBody *bodiesData[BODY_COUNT] = {};

	if (SUCCEEDED(result)) {
		Eigen::RowVector3f y(floorPlane.x, floorPlane.y, floorPlane.z);
		Eigen::RowVector3f z = Eigen::Vector3f(0, 1, -floorPlane.y / floorPlane.z).normalized();
		Eigen::RowVector3f x = y.cross(z);

		rotation << x, y, z;

		result = bodyFrame->GetAndRefreshBodyData(BODY_COUNT, bodiesData);
	}

	for (int bodyIndex = 0; bodyIndex < BODY_COUNT; bodyIndex++) {
		IBody *bodyData = bodiesData[bodyIndex];
		BOOLEAN tracked;

		if (SUCCEEDED(result)) {
			result = bodyData->get_IsTracked(&tracked);
		}

		Body &body = bodies[bodyIndex];

		if (SUCCEEDED(result)) {
			body.tracked = tracked;

			if (tracked) {
				result = bodyData->GetJoints(JointType_Count, body.joints);

				if (SUCCEEDED(result)) {
					for (int jointIndex = 0; jointIndex < JointType_Count; jointIndex++) {
						Joint &joint = body.joints[jointIndex];
						CameraSpacePoint &point = joint.Position;

						Eigen::Vector3f location = rotation * Eigen::Vector3f(point.X, point.Y, point.Z);
						location[1] += floorPlane.w;

						Filter *&filter = body.filters[jointIndex];

						if (filter) {
							filter->Update((current - body.previous) / 10000000.0, processNoise, observationNoise, location);
						} else {
							filter = new Filter(location);
						}

						point.X = location[0];
						point.Y = location[1];
						point.Z = location[2];
					}

					body.previous = current;
				}
			}
		}

		Release(bodyData);
	}

	Release(bodyFrame);

	return result;
}

HRESULT Close() {
	if (!sensor) {
		return E_FAIL;
	}

	for (Body &body : bodies) {
		for (Filter *&filter : body.filters) {
			delete filter;
			filter = NULL;
		}
	}

	Release(bodyFrameReader);
	
	HRESULT result = sensor->Close();
	Release(sensor);

	return result;
}

PYBIND11_MODULE(kinect, module) {
	pybind11::class_<Joint>(module, "Joint")
		.def_property_readonly("x", [](Joint joint){return joint.Position.X;})
		.def_property_readonly("y", [](Joint joint){return joint.Position.Y;})
		.def_property_readonly("z", [](Joint joint){return joint.Position.Z;});
	
	pybind11::class_<Body>(module, "Body")
		.def_readonly("tracked", &Body::tracked)
		.def_property_readonly("joints", [](Body body){
			pybind11::list joints;

			for (Joint &joint : body.joints) {
				joints.append(joint);
			}

			return joints;
		});

	module.def("open", &Open);
	module.def("update", &Update);

	module.def("getBodies", [](){
		pybind11::list bodies;

		for (Body &body : ::bodies) {
			bodies.append(body);
		}

		return bodies;
	});

	module.def("close", &Close);
}