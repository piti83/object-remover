#pragma once

#include <vector>

#include <opencv2/core.hpp>

namespace object_remover {

struct Object {
    int id = 0;
    cv::Point2d centroid;  // (x, y), origin at top-left
    cv::Rect bbox;
    int area = 0;          // pixels
};

// Labels connected components of a binary mask and measures each one.
std::vector<Object> analyse(const cv::Mat& mask, int connectivity = 8);

}  // namespace object_remover
