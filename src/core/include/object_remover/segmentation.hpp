#pragma once

#include <opencv2/core.hpp>

namespace object_remover {

// Colour image (BGR) -> binary foreground mask (CV_8UC1, 0/255).
// TODO: channel selection (gray / HSV S), smoothing, Otsu, auto-invert for light background.
cv::Mat segment(const cv::Mat& bgr);

}  // namespace object_remover
