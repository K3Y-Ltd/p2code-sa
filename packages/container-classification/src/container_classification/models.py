import torch
import torch.nn as nn
import torchvision.models as models

from torchvision.models import (
    AlexNet_Weights,
    ResNet18_Weights,
    MobileNet_V2_Weights,
    SqueezeNet1_1_Weights,
    VGG11_Weights, ShuffleNet_V2_X1_0_Weights,
    EfficientNet_B0_Weights,
    ResNeXt101_32X8D_Weights
)


class AlexNet(nn.Module):

    def __init__(self):
        """
        Initializes an AlexNet-based model for binary classification.
        """
        super().__init__()
        self.pretrained_model = models.alexnet()
        self.pooling_layer = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(256, 2)

    def load_pretrained_weights(self, mode="default"):
        """
        Load pretrained weights.
        """
        self.pretrained_model = models.alexnet(weights=AlexNet_Weights.DEFAULT)

    def forward(self, x):
        """
        Forward method for the `AlexNet` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input plane mri slices

        Returns
        -------
        output : torch.tensor
            Logits scores for the two classes.
        """
        features = self.pretrained_model.features(x)

        pooled_features = self.pooling_layer(features)
        pooled_features = pooled_features.view(pooled_features.size(0), -1)
        
        output = self.classifier(pooled_features)
        
        return output


class ResNet18(nn.Module):

    def __init__(self, num_classes=2):
        """
        Initializes n Resnet-based model for binary classification.
        """
        super(ResNet18, self).__init__()
        resnet = models.resnet18(weights=ResNet18_Weights.DEFAULT)

        resnet.fc = nn.Sequential(
            nn.Linear(resnet.fc.in_features, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes),
        )
        self.resnet = resnet

    def forward(self, x):
        """
        Forward method for the `ResNet18` torch module.

        Parameters
        ----------
        x : torch.tensor
            The input plane mri slices

        Returns
        -------
        output : torch.tensor
            Binary output classification scores.
        """
        return self.resnet(x)


class MobileNetV2(nn.Module):
    def __init__(self, num_classes=2):
        """
        Initializes a MobileNetV2 model for binary classification.
        """
        super(MobileNetV2, self).__init__()
        mobilenet = models.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
        # Replace the final classification layer with a new one suitable for the number of classes
        mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.2), nn.Linear(mobilenet.last_channel, num_classes)
        )
        self.mobilenet = mobilenet

    def forward(self, x):
        """
        Forward method for the `MobileNetV2` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input plane mri slices

        Returns
        -------
        output : torch.tensor
            Binary output classification scores
        """
        return self.mobilenet(x)


class SqueezeNet(nn.Module):
    def __init__(self, num_classes=2):
        """
        Initializes the SqueezeNet model for fine-tuning.

        Args:
            num_classes (int): The number of classes for classification.
            feature_extracting (bool): If True, only updates the final layer,
                                       freezes other layers.
            use_pretrained (bool): If True, uses a pre-trained model.
        """

        # Load the pre-trained SqueezeNet model
        super(SqueezeNet, self).__init__()
        self.squeezenet = models.squeezenet1_1(weights=SqueezeNet1_1_Weights.DEFAULT)
        self.squeezenet.classifier[1] = nn.Conv2d(512, num_classes, kernel_size=(1, 1), stride=(1, 1))

    def forward(self, x):
        """
        Forward method for the `MobileNetV2` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input plane mri slices

        Returns
        -------
        output : torch.tensor
            Binary output classification scores
        """
        return self.squeezenet(x)


class VGG11(nn.Module):
    def __init__(self, num_classes=2):
        """
        Initializes a VGG11 model for binary classification.
        """
        super(VGG11, self).__init__()
        vgg11 = models.vgg11(weights=VGG11_Weights.DEFAULT)
        # Replace the final classifier layer to match the number of output classes
        vgg11.classifier[6] = nn.Linear(vgg11.classifier[6].in_features, num_classes)
        self.vgg11 = vgg11

    def forward(self, x):
        """
        Forward method for the `VGG11` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input images

        Returns
        -------
        output : torch.tensor
            Binary output classification scores
        """
        return self.vgg11(x)



class EfficientNet(nn.Module):
    def __init__(self, num_classes=2):
        """
        Initializes an EfficientNet-B0 model for binary classification.
        """
        super(EfficientNet, self).__init__()
        # Load the pre-trained EfficientNet-B0 model
        efficientnet = models.efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)

        # Replace the final classifier layer to match the number of output classes
        efficientnet.classifier[1] = nn.Linear(efficientnet.classifier[1].in_features, num_classes)

        self.efficientnet = efficientnet


    def forward(self, x):
        """
        Forward method for the `EfficientNet` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input images

        Returns
        -------
        output : torch.tensor
            Binary output classification scores
        """
        return self.efficientnet(x)


class ShuffleNet(nn.Module):
    def __init__(self, num_classes=2):
        """
        Initializes a ShuffleNetV2 model for binary classification.
        """
        super(ShuffleNet, self).__init__()
        # Load the pre-trained ShuffleNetV2 model
        shufflenet = models.shufflenet_v2_x1_0(weights=ShuffleNet_V2_X1_0_Weights.DEFAULT)

        # Replace the final classifier layer to match the number of output classes
        shufflenet.fc = nn.Linear(shufflenet.fc.in_features, num_classes)

        self.shufflenet = shufflenet

    def forward(self, x):
        """
        Forward method for the `ShuffleNet` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input images

        Returns
        -------
        output : torch.tensor
            Binary output classification scores
        """
        return self.shufflenet(x)

class ResNext101(nn.Module):
    def __init__(self, num_classes=2):
        """
        Initializes a ShuffleNetV2 model for binary classification.
        """
        super(ResNext101, self).__init__()
        # Load the pre-trained ShuffleNetV2 model
        resnext = models.resnext101_32x8d(weights=ResNeXt101_32X8D_Weights.DEFAULT)
        # Replace the final fully connected layer to match the number of output classes
        resnext.fc = nn.Linear(resnext.fc.in_features, num_classes)

        self.resnext = resnext


    def forward(self, x):
        """
        Forward method for the `ShuffleNet` torch module.

        Parameters
        ----------
        x: torch.tensor
            The input images

        Returns
        -------
        output : torch.tensor
            Binary output classification scores
        """
        return self.resnext(x)



if __name__== "__main__":
    model = ResNext101()
    a = torch.randn((1, 3, 256, 256))
    out = model(a)